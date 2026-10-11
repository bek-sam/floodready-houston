import asyncio
import time

from app.services import diskcache
from app.services.http import get_json

CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

# Pre-seeded demo addresses (approximate coordinates) so the demo never depends on a live geocoder.
SEEDS = {
    "4800 calhoun rd": {"lat": 29.7199, "lon": -95.3422, "matched_address": "4800 CALHOUN RD, HOUSTON, TX, 77004 (University of Houston)"},
    "meyerland": {"lat": 29.6786, "lon": -95.4640, "matched_address": "Meyerland, Houston, TX"},
    "901 bagby st": {"lat": 29.7607, "lon": -95.3695, "matched_address": "901 BAGBY ST, HOUSTON, TX, 77002"},
}
_last_nominatim = 0.0
_lock = asyncio.Lock()


def _key(q: str) -> str:
    return " ".join(q.lower().replace(",", " ").split())


def _seed_hit(k: str):
    for s, v in SEEDS.items():
        if k.startswith(s):
            return v
    return None


async def geocode(q: str) -> dict:
    """Returns {lat, lon, matched_address, ...}; lat/lon None if not found. Cached (memory + disk)."""
    global _last_nominatim
    k = _key(q)
    hit = diskcache.get("geocode", k) or _seed_hit(k)
    if hit:
        return dict(hit)
    warnings = []
    d = await get_json(CENSUS, {"address": q, "benchmark": "Public_AR_Current", "format": "json"}, ttl=3600)
    try:
        m = d["result"]["addressMatches"][0]
        out = {"lat": m["coordinates"]["y"], "lon": m["coordinates"]["x"], "matched_address": m["matchedAddress"]}
        out["place"] = (m.get("addressComponents") or {}).get("city")
        diskcache.put("geocode", k, out)
        return out
    except Exception:
        warnings.append("Census geocoder had no match; tried Nominatim")
    async with _lock:  # Nominatim policy: max 1 request/second
        wait = 1.1 - (time.time() - _last_nominatim)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_nominatim = time.time()
        d = await get_json(NOMINATIM, {"q": q, "format": "json", "limit": 1, "countrycodes": "us"}, ttl=3600)
    try:
        m = d[0]
        out = {"lat": float(m["lat"]), "lon": float(m["lon"]), "matched_address": m["display_name"]}
        diskcache.put("geocode", k, out)
        return {**out, "warnings": warnings}
    except Exception:
        warnings.append("No geocoding result")
        return {"lat": None, "lon": None, "matched_address": None, "warnings": warnings}
