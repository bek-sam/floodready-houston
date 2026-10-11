"""GET /api/status: per-source health (passive request tracking + light cached probes) and snapshot dates."""
import asyncio
import os
import time

from fastapi import APIRouter

from app import freshness
from app.services.gauges import load_gauges
from app.services.http import get_json

router = APIRouter()

CACHE_S = 60
SOURCES = ["NWS", "USGS OGC", "NOAA NWPS", "FEMA NFHL", "USGS EPQS", "Census geocoder", "OSRM", "OpenFEMA", "ArcGIS layers"]
_cache = {"t": 0.0, "data": None}
_probing = False


def _probes() -> dict:
    lid = next((g.get("id") for g in load_gauges() if g.get("id")), "ADDT2")
    return {
        "NWS": ("https://api.weather.gov/alerts/active/count", None),
        "USGS OGC": ("https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-continuous/items",
                     {"monitoring_location_id": "USGS-08074500", "parameter_code": "00065", "f": "json", "limit": 1}),
        "NOAA NWPS": (f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}", None),
        "FEMA NFHL": ("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28", {"f": "json"}),
        "USGS EPQS": ("https://epqs.nationalmap.gov/v1/json", {"x": -95.37, "y": 29.76, "units": "Feet", "wkid": 4326}),
        "Census geocoder": ("https://geocoding.geo.census.gov/geocoder/benchmarks", {"format": "json"}),
        "OSRM": ("https://router.project-osrm.org/route/v1/driving/-95.37,29.76;-95.36,29.75", {"overview": "false"}),
        "OpenFEMA": ("https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries", {"$top": 1}),
        "ArcGIS layers": ("https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services/City_Limit_Boundaries_FL/FeatureServer/0", {"f": "json"}),
    }


async def probe_all() -> None:
    """Fire light GETs (ttl=0 so they hit the network and record health). Never raises."""
    global _probing
    if _probing:
        return
    _probing = True
    try:
        await asyncio.wait_for(asyncio.gather(*[get_json(u, p, ttl=0) for u, p in _probes().values()],
                                              return_exceptions=True), timeout=12)
    except Exception:
        pass
    finally:
        _probing = False


def _db_ok() -> dict:
    t0 = time.time()
    try:
        from sqlalchemy import text
        from app.db import get_session
        with get_session() as s:
            s.execute(text("SELECT 1"))
        freshness.record("DB", True, (time.time() - t0) * 1000)
    except Exception as e:
        freshness.record("DB", False, 0, type(e).__name__)
    return freshness.health("DB")


def build() -> dict:
    sources = {n: freshness.health(n) for n in SOURCES}
    sources["DB"] = _db_ok()
    for n, env in (("Gemini", "GEMINI_API_KEY"), ("ElevenLabs", "ELEVENLABS_API_KEY")):
        sources[n] = {"configured": bool(os.getenv(env)), "circuit": "not_used" if os.getenv(env) else "unconfigured",
                      "last_success": None, "last_error": None, "p50_ms": None}
    try:
        from app.ai.config import quota_status
        sources["Gemini"] = {**sources["Gemini"], "configured": bool(quota_status()["keys"]), **quota_status()}
    except Exception:  # noqa: BLE001
        pass
    return {"sources": [{"name": n, **h} for n, h in sources.items()],
            "snapshots": freshness.snapshot_dates(), "storm_mode": freshness.storm_on(),
            "meta": freshness.meta("FloodReady source health", "live")}


async def _refresh() -> None:
    await probe_all()
    _cache["data"] = build()


@router.get("/status")
async def status():
    if time.time() - _cache["t"] > CACHE_S:
        _cache["t"] = time.time()
        asyncio.create_task(_refresh())   # background probes; the response never waits on them
        if _cache["data"] is None:
            _cache["data"] = build()
    return _cache["data"]
