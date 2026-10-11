"""Gauge stage time series: background poller (USGS OGC) -> gauge_readings table; history API."""
import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

import httpx

from app.config import USER_AGENT
from app import freshness
from app.db import GaugeReading, get_session
from app.services.gauges import load_gauges

log = logging.getLogger("gauge_history")
OGC = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/{coll}/items"
INTERVAL_S = 15 * 60
BATCH = 20
TIMEOUT = 15.0
MIN_DB_POINTS = 3
SOURCE = "https://api.waterdata.usgs.gov/ogcapi/v0/"


_LAST_APPROVAL: dict = {}


def _gid(g):
    return g.get("id") or g.get("nwps_id") or g.get("lid")


def _parse(features: list) -> list[tuple[str, datetime, float]]:
    out = []
    for f in features or []:
        try:
            p = f["properties"]
            usgs = str(p["monitoring_location_id"]).replace("USGS-", "")
            t = datetime.fromisoformat(str(p["time"]).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            v = float(p["value"])
            _LAST_APPROVAL[usgs] = (p.get("approval_status"), p.get("qualifier"))
            if v > -900:
                out.append((usgs, t, v))
        except Exception:
            continue
    return out


async def _fetch(client: httpx.AsyncClient, coll: str, ids: list[str], extra: dict) -> list:
    params = {"monitoring_location_id": ",".join(f"USGS-{i}" for i in ids), "parameter_code": "00065",
              "f": "json", **extra}
    try:
        t0 = time.time()
        r = await client.get(OGC.format(coll=coll), params=params)
        r.raise_for_status()
        out = _parse(r.json().get("features", []))
        freshness.record("USGS OGC", True, (time.time() - t0) * 1000)
        return out
    except Exception as e:
        freshness.record("USGS OGC", False, 0, type(e).__name__)
        log.warning("USGS %s fetch failed: %s", coll, e)
        return []


def _client():
    return httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT})


def _store(rows: list[tuple[str, datetime, float]]) -> int:
    """Insert rows not already present. Returns number inserted."""
    if not rows:
        return 0
    s = get_session()
    try:
        keys = {(r.gauge_id, r.t.replace(tzinfo=None) if r.t.tzinfo else r.t) for r in
                s.query(GaugeReading).filter(GaugeReading.t >= min(t for _, t, _ in rows) - timedelta(minutes=1))}
        n = 0
        for gid, t, v in rows:
            if (gid, t.replace(tzinfo=None)) in keys:
                continue
            keys.add((gid, t.replace(tzinfo=None)))
            s.add(GaugeReading(gauge_id=gid, t=t, stage_ft=v))
            n += 1
        s.commit()
        return n
    except Exception as e:
        s.rollback()
        log.warning("store failed: %s", e)
        return 0
    finally:
        s.close()


async def poll_once() -> int:
    """One poll: latest value for every gauge with a usgs_id, in batches. Never raises."""
    try:
        by_usgs = {str(g["usgs_id"]): _gid(g) for g in load_gauges() if g.get("usgs_id")}
        ids = list(by_usgs)
        rows = []
        async with _client() as c:
            for i in range(0, len(ids), BATCH):
                got = await _fetch(c, "latest-continuous", ids[i:i + BATCH], {"limit": 500})
                rows += [(by_usgs[u], t, v) for u, t, v in got if u in by_usgs]
                await asyncio.sleep(0.5)
        return await asyncio.to_thread(_store, rows)
    except Exception as e:
        log.warning("poll failed: %s", e)
        return 0


async def poll_loop():
    await asyncio.sleep(20)  # never block startup
    while True:
        try:
            await poll_once()
        except Exception as e:
            log.warning("poll loop error: %s", e)
        await asyncio.sleep(INTERVAL_S)


def _read_db(gid: str, since: datetime) -> list[dict]:
    s = get_session()
    try:
        q = s.query(GaugeReading).filter(GaugeReading.gauge_id == gid, GaugeReading.t >= since)
        return [{"t": r.t.replace(tzinfo=timezone.utc).isoformat() if r.t.tzinfo is None else r.t.isoformat(),
                 "stage_ft": r.stage_ft} for r in q.order_by(GaugeReading.t)]
    except Exception as e:
        log.warning("db read failed: %s", e)
        return []
    finally:
        s.close()


async def history(gauge_id: str, hours: int = 48) -> dict | None:
    g = next((g for g in load_gauges() if _gid(g) == gauge_id or str(g.get("usgs_id")) == gauge_id), None)
    if g is None:
        return None
    gid = _gid(g)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    readings = await asyncio.to_thread(_read_db, gid, since)
    source = "db"
    if len(readings) < MIN_DB_POINTS:
        source = "live"
        readings = []
        if g.get("usgs_id"):
            async with _client() as c:
                got = await _fetch(c, "continuous", [str(g["usgs_id"])],
                                   {"time": f"PT{hours}H", "limit": 1000})
            readings = sorted(({"t": t.isoformat(), "stage_ft": v} for _, t, v in got), key=lambda r: r["t"])
    st = g.get("flood_stages") or {}
    pts = [(freshness._parse(r["t"]), r["stage_ft"]) for r in readings]
    appr, qual = _LAST_APPROVAL.get(str(g.get("usgs_id")), (None, None))
    flags = freshness.gauge_flags(readings[-1]["t"] if readings else None, pts, appr, [qual] if qual else None)
    flags["offline"] = not readings or flags["stale"]
    return {"id": gid, "name": g.get("name"), "readings": readings, "source": source, **flags,
            "observed_at": readings[-1]["t"] if readings else None,
            "meta": freshness.meta(SOURCE, "live" if source == "live" else "recent",
                                   as_of=readings[-1]["t"] if readings else None),
            "flood_stages": {k: st.get(k) for k in ("action", "minor", "moderate", "major")},
            "data_source": SOURCE}
