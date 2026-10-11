"""Freshness metadata, storm mode, gauge quality flags and per-source health tracking.

Everything here is passive and never raises: data endpoints call meta()/gauge_flags(), and services/http.py
calls record() after every outbound request so /api/status can report health without extra traffic.
"""
import json
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from app.config import DATA_DIR

STALE_HOURS = 2
PROVISIONAL_DAYS = 120
SPIKE_FT = 3.0
SPIKE_MINUTES = 15
STORM_TTL = 90          # seconds; cache TTL cap for alerts/gauges/risk sources during storm mode
STORM_HOLD = 180        # seconds the global storm flag stays on after last trigger
STORM_HOSTS = ("api.weather.gov", "api.water.noaa.gov", "api.waterdata.usgs.gov", "hazards.fema.gov")

_storm_until = 0.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def mark_storm() -> None:
    global _storm_until
    _storm_until = time.time() + STORM_HOLD


def storm_on() -> bool:
    return time.time() < _storm_until


def clear_storm() -> None:
    global _storm_until
    _storm_until = 0.0


def effective_ttl(url: str, ttl: float) -> float:
    if ttl > 0 and storm_on() and urlparse(url).hostname in STORM_HOSTS:
        return min(ttl, STORM_TTL)
    return ttl


def meta(source: str, freshness: str = "live", as_of: str | None = None, snapshot_date: str | None = None,
         storm: bool | None = None) -> dict:
    m = {"as_of": as_of or now_iso(), "source": source, "freshness": freshness,
         "storm_mode": storm_on() if storm is None else bool(storm)}
    if snapshot_date:
        m["snapshot_date"] = snapshot_date
    return m


def with_meta(d, **kw):
    """Attach meta to a dict response (additive). Non-dicts are returned untouched."""
    if isinstance(d, dict):
        d["meta"] = meta(**kw)
    return d


# ---------- snapshots ----------
SNAP_FILES = {"crossings": "crossings.geojson", "harvey": "harvey/coverage.json", "dialysis": "dialysis.json",
              "shelters": "shelters.json", "civic": "civic.json", "knowledge": "knowledge"}


def snapshot_dates() -> dict:
    """Date (YYYY-MM-DD) per snapshot: manifest.json when present, else the file's mtime."""
    out = {}
    man = {}
    try:
        man = json.loads((DATA_DIR / "snapshots" / "manifest.json").read_text()).get("snapshots", {})
    except Exception:
        pass
    for k, rel in SNAP_FILES.items():
        d = (man.get(k) or {}).get("date")
        if not d:
            try:
                p = DATA_DIR / rel
                if k == "harvey":
                    d = json.loads(p.read_text()).get("fetched_at", "")[:10]
                elif k == "knowledge":
                    d = datetime.fromtimestamp(max(f.stat().st_mtime for f in p.glob("*.md")), timezone.utc).date().isoformat()
                else:
                    d = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).date().isoformat()
            except Exception:
                d = None
        out[k] = d
    return out


def snap_meta(key: str, source: str) -> dict:
    d = snapshot_dates().get(key)
    return meta(source, "snapshot", as_of=(d + "T00:00:00+00:00") if d else None, snapshot_date=d, storm=False)


# ---------- gauge quality flags ----------
def _parse(t):
    try:
        x = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def gauge_flags(observed_at, series: list | None = None, approval: str | None = None, qualifiers=None) -> dict:
    """series: [(datetime, value)] ascending. Returns {stale, offline, provisional, spike[, qualifiers]}."""
    now = datetime.now(timezone.utc)
    t = _parse(observed_at)
    stale = t is None or now - t > timedelta(hours=STALE_HOURS)
    prov = bool(t) and (now - t) <= timedelta(days=PROVISIONAL_DAYS)
    if approval:
        prov = approval.lower().startswith("prov") or (prov and approval.lower() != "approved")
    spike = False
    pts = [p for p in (series or []) if p[0] is not None]
    for (t1, v1), (t2, v2) in zip(pts, pts[1:]):
        if timedelta(0) < t2 - t1 <= timedelta(minutes=SPIKE_MINUTES) and abs(v2 - v1) > SPIKE_FT:
            spike = True
    out = {"stale": stale, "provisional": prov, "spike": spike}
    if qualifiers:
        out["qualifiers"] = list(qualifiers)
    return out


# ---------- source health ----------
def source_for(url: str) -> str | None:
    h = urlparse(url).hostname or ""
    if h == "api.weather.gov":
        return "NWS"
    if h == "api.waterdata.usgs.gov":
        return "USGS OGC"
    if h == "api.water.noaa.gov":
        return "NOAA NWPS"
    if h == "hazards.fema.gov":
        return "FEMA NFHL"
    if h == "epqs.nationalmap.gov":
        return "USGS EPQS"
    if h == "geocoding.geo.census.gov":
        return "Census geocoder"
    if "osrm" in h:
        return "OSRM"
    if h.endswith("fema.gov"):
        return "OpenFEMA"
    if "arcgis" in h or h.endswith(".gov") and "gis" in h:
        return "ArcGIS layers"
    if h == "api.open-meteo.com":
        return "Open-Meteo"
    return None


class _H:
    def __init__(self):
        self.last_success = None
        self.last_error = None
        self.last_error_msg = None
        self.lat = deque(maxlen=50)
        self.fails = 0


_health: dict[str, _H] = {}
CIRCUIT_FAILS = 5


def record(source: str | None, ok: bool, latency_ms: float, err: str | None = None) -> None:
    if not source:
        return
    h = _health.setdefault(source, _H())
    if ok:
        h.last_success, h.fails = now_iso(), 0
        h.lat.append(latency_ms)
    else:
        h.last_error, h.last_error_msg, h.fails = now_iso(), (err or "")[:120], h.fails + 1


def health(source: str) -> dict:
    h = _health.get(source)
    if not h:
        return {"last_success": None, "last_error": None, "p50_ms": None, "circuit": "unknown"}
    lat = sorted(h.lat)
    circuit = "open" if h.fails >= CIRCUIT_FAILS else ("half_open" if h.fails > 0 else "closed")
    return {"last_success": h.last_success, "last_error": h.last_error, "last_error_msg": h.last_error_msg,
            "p50_ms": round(lat[len(lat) // 2]) if lat else None, "circuit": circuit}


def reset_health() -> None:
    _health.clear()
