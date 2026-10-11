"""Who represents/administers a point: commissioner, Houston council, floodplain administrator. Never raises."""
import asyncio
import time

from app.services.arcgis import HCFCD
from app.services.http import get_json

TTL = 24 * 3600
PRECINCT_URL = "https://www.gis.hctx.net/arcgis/rest/services/CommPrecinct/MapServer/0/query"
COUNCIL_URL = f"{HCFCD}/City_of_Houston_Council_Districts/FeatureServer/0/query"
ADMIN_URL = f"{HCFCD}/Floodplain_Administrators/FeatureServer/0/query"


async def _at(url: str, lat: float, lon: float, fields: str) -> dict | None:
    d = await get_json(url, {"geometry": f"{lon:.4f},{lat:.4f}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                             "spatialRel": "esriSpatialRelIntersects", "outFields": fields,
                             "returnGeometry": "false", "f": "json"}, ttl=TTL)
    try:
        return d["features"][0]["attributes"]
    except Exception:
        return None


def _clean_phone(p):
    return p.replace("Phone:", "").strip() if isinstance(p, str) and p.strip() else None


_cache: dict = {}
CACHE_TTL = 3600
PART_TIMEOUT = 4


async def _safe(coro):
    try:
        return await asyncio.wait_for(coro, PART_TIMEOUT)
    except Exception:
        return None


async def get_officials(lat: float, lon: float) -> dict:
    key = (round(lat, 3), round(lon, 3))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    out: dict = {"commissioner": None, "council": None, "floodplain_admin": None}
    try:
        # all three lookups run concurrently; council is nulled afterwards if the point is not in City of Houston
        a, adm, c = await asyncio.gather(
            _safe(_at(PRECINCT_URL, lat, lon, "PCT_NO,COMMISSION,URL")),
            _safe(_at(ADMIN_URL, lat, lon, "Entity,Administrator,Phone,Email,Address")),
            _safe(_at(COUNCIL_URL, lat, lon, "DISTRICT,MEMBER,PHONE")))
        if a:
            out["commissioner"] = {"precinct": a.get("PCT_NO"), "name": a.get("COMMISSION"), "url": a.get("URL")}
        if adm:
            out["floodplain_admin"] = {"name": adm.get("Administrator"), "entity": adm.get("Entity"),
                                       "phone": _clean_phone(adm.get("Phone")), "email": adm.get("Email"),
                                       "address": adm.get("Address"),
                                       "url": "https://www.hcfcd.org/Find-Your-Floodplain-Administrator"}
        if c and adm and adm.get("Entity") == "City of Houston":  # council districts only valid inside city limits
            member = (c.get("MEMBER") or "").strip().title() or None
            out["council"] = {"district": c.get("DISTRICT"), "member": member,
                              "phone": c.get("PHONE"), "url": "https://www.houstontx.gov/council/"}
    except Exception:
        pass
    if out["commissioner"] or out["floodplain_admin"]:  # don't cache total failure
        _cache[key] = (time.time(), out)
    return out
