"""Flood history at a point: Harvey extent + nearest replay-gauge peaks per event + ZIP claims peak year."""
import asyncio
import json
import logging
import time

from app import config
from app.services.data import haversine_m
from app.services.harvey import harvey_at
from app.services.risk import _juris, harvey_for_jurisdiction, jurisdiction_name
from app.services.zipinsurance import valid_zip, zip_insurance

log = logging.getLogger("floodhistory")
MAX_MI = 5.0
ORDER = ["action", "minor", "moderate", "major"]


def peak_category(peak, stages: dict | None) -> str:
    stages = stages or {}
    cat = "normal"
    for k in ORDER:
        v = stages.get(k)
        if v is not None and peak >= v:
            cat = k
    return cat


def _events() -> list[dict]:
    out = []
    for p in sorted((config.DATA_DIR / "replay").glob("*.json")):
        if p.name == "events.json":
            continue
        try:
            d = json.loads(p.read_text())
            out.append(d)
        except Exception as e:
            log.warning("replay %s unreadable: %s", p.name, e)
    return sorted(out, key=lambda d: (d.get("event") or {}).get("start") or "")


def _nearest(lat, lon, gauges):
    best = None
    for g in gauges:
        try:
            vals = [x["stage_ft"] for x in g.get("series") or [] if x.get("stage_ft") is not None]
            if not vals:
                continue
            mi = haversine_m(lat, lon, g["lat"], g["lon"]) / 1609.344
        except Exception:
            continue
        if mi <= MAX_MI and (best is None or mi < best[0]):
            best = (mi, g, max(vals))
    return best


_cache: dict = {}
CACHE_TTL = 24 * 3600


async def flood_history(lat: float, lon: float, zip_code: str | None = None) -> dict:
    """24 h in-memory cache by (lat,lon 3 dp, zip); full results only (partial/warned results are not cached)."""
    key = (round(lat, 3), round(lon, 3), zip_code or "")
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    out = await _flood_history(lat, lon, zip_code)
    if not out.get("warnings"):
        _cache[key] = (time.time(), out)
    return out


async def _flood_history(lat: float, lon: float, zip_code: str | None = None) -> dict:
    warnings = []
    events = []
    for d in _events():
        ev = d.get("event") or {}
        n = _nearest(lat, lon, d.get("gauges") or [])
        ng = None
        if n:
            mi, g, peak = n
            ng = {"id": g.get("id"), "name": g.get("name"), "distance_mi": round(mi, 1),
                  "peak_ft": round(peak, 2), "peak_category": peak_category(peak, g.get("flood_stages"))}
        events.append({"id": ev.get("id"), "name": ev.get("name"), "start": ev.get("start"), "nearest_gauge": ng})
    zip_out = None
    if zip_code and valid_zip(zip_code):
        try:
            z = await asyncio.wait_for(zip_insurance(zip_code), 8)
            by_year = (z.get("claims") or {}).get("by_year") or []
            if by_year:
                top = max(by_year, key=lambda r: r["count"])
                if top["count"] > 0:
                    zip_out = {"zip": zip_code, "peak_year": top["year"], "peak_year_claims": top["count"]}
        except Exception as e:
            log.warning("zip lookup failed: %s", e)
            warnings.append("ZIP claims history timed out or is unavailable; showing the rest")
    h = harvey_at(lat, lon)
    if h.get("flooded") is False:
        try:
            h = harvey_for_jurisdiction(h, jurisdiction_name(await _juris(lat, lon)))
        except Exception as e:
            log.warning("jurisdiction lookup failed: %s", e)
    out = {"harvey": {"flooded": h.get("flooded"), "source": h.get("source")}, "events": events, "zip": zip_out}
    if warnings:
        out["warnings"] = warnings
    return out
