"""Live gauge status: NWPS stageflow (primary) vs flood stages in data/gauges.json."""
import asyncio
from datetime import datetime, timedelta, timezone

from app import freshness
from app.services.data import haversine_m, load_json
from app.services.http import get_json

NWPS = "https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow"
ORDER = ["normal", "action", "minor", "moderate", "major"]


def load_gauges() -> list[dict]:
    d = load_json("gauges.json", [])
    if isinstance(d, dict):
        d = d.get("gauges", [])
    return [g for g in d if isinstance(g, dict) and g.get("lat") is not None and g.get("lon") is not None]


def classify(stage, stages: dict | None) -> str:
    if stage is None:
        return "unknown"
    stages = stages or {}
    status = "normal"
    for name in ("action", "minor", "moderate", "major"):
        v = stages.get(name)
        if v is not None and stage >= v:
            status = name
    return status


def _stale(valid_time: str, hours: float = 6) -> bool:
    try:
        t = datetime.fromisoformat(str(valid_time).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - t > timedelta(hours=hours)
    except Exception:
        return False


_impacts: dict | None = None


def _impact_for(gid, stage) -> dict | None:
    global _impacts
    if _impacts is None:
        d = load_json("gauge_impacts.json", {})
        _impacts = d if isinstance(d, dict) else {}
    e = _impacts.get(gid) if gid else None
    if not isinstance(e, dict):
        return None
    imps = sorted((i for i in e.get("impacts") or [] if isinstance(i, dict) and i.get("stage") is not None),
                  key=lambda i: i["stage"])
    cur = nxt = None
    if stage is not None:
        below = [i for i in imps if i["stage"] <= stage]
        above = [i for i in imps if i["stage"] > stage]
        cur = {"stage": below[-1]["stage"], "statement": below[-1].get("statement")} if below else None
        nxt = {"stage": above[0]["stage"], "statement": above[0].get("statement")} if above else None
    elif imps:
        nxt = None
    crest = (e.get("harvey_crest") or {}).get("stage")
    return {"current": cur, "next": nxt, "harvey_crest_ft": crest,
            "harvey_delta_ft": round(crest - stage, 2) if crest is not None and stage is not None else None,
            "source": e.get("source") or f"https://water.noaa.gov/gauges/{gid}"}


def _gid(g):
    return g.get("id") or g.get("nwps_id") or g.get("lid")


async def gauge_status(g: dict, simulate: bool = False) -> dict:
    stages = g.get("flood_stages") or {}
    stage, observed, series = None, None, []
    lid = g.get("nwps_id") or g.get("lid") or g.get("id")
    d = await get_json(NWPS.format(lid=lid), ttl=300) if lid else None
    try:
        obs = d["observed"]["data"]
        valid = [o for o in obs if o.get("primary") is not None and o["primary"] > -900]
        last = valid[-1]
        stage, observed = float(last["primary"]), last.get("validTime")
        for o in valid[-8:]:
            t = freshness._parse(o.get("validTime"))
            if t:
                series.append((t, float(o["primary"])))
    except Exception:
        pass
    flags = freshness.gauge_flags(observed, series)
    offline = stage is None or (observed and _stale(observed))
    if stage is not None and observed and _stale(observed):
        stage = None
    if simulate and stages.get("minor") is not None:
        stage, observed = float(stages["minor"]) + 0.5, "simulated"
        flags = {"stale": False, "provisional": False, "spike": False}
        offline = False
    status = classify(stage, stages)
    if status not in ("normal", "unknown") and not simulate:
        freshness.mark_storm()
    flags["offline"] = bool(offline)
    return {"id": _gid(g), "name": g.get("name"), "lat": g["lat"], "lon": g["lon"], "stage_ft": stage,
            "observed_at": observed, "flood_stages": {k: stages.get(k) for k in ("action", "minor", "moderate", "major")},
            "status": status, **flags, "impact": _impact_for(_gid(g), stage)}


async def nearest_gauges(lat: float, lon: float, n: int = 3, simulate: bool = False) -> list[dict]:
    gs = sorted(load_gauges(), key=lambda g: haversine_m(lat, lon, g["lat"], g["lon"]))[:n]
    return list(await asyncio.gather(*[gauge_status(g, simulate) for g in gs]))
