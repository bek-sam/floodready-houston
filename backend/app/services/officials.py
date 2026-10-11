"""Who represents/administers a point: commissioner, Houston council, floodplain administrator. Never raises."""
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


async def get_officials(lat: float, lon: float) -> dict:
    out: dict = {"commissioner": None, "council": None, "floodplain_admin": None}
    try:
        a = await _at(PRECINCT_URL, lat, lon, "PCT_NO,COMMISSION,URL")
        if a:
            out["commissioner"] = {"precinct": a.get("PCT_NO"), "name": a.get("COMMISSION"), "url": a.get("URL")}
        adm = await _at(ADMIN_URL, lat, lon, "Entity,Administrator,Phone,Email,Address")
        if adm:
            out["floodplain_admin"] = {"name": adm.get("Administrator"), "entity": adm.get("Entity"),
                                       "phone": _clean_phone(adm.get("Phone")), "email": adm.get("Email"),
                                       "address": adm.get("Address"),
                                       "url": "https://www.hcfcd.org/Find-Your-Floodplain-Administrator"}
        if adm and adm.get("Entity") == "City of Houston":  # council districts only valid inside city limits
            c = await _at(COUNCIL_URL, lat, lon, "DISTRICT,MEMBER,PHONE")
            if c:
                out["council"] = {"district": c.get("DISTRICT"), "member": (c.get("MEMBER") or "").title(),
                                  "phone": c.get("PHONE"), "url": "https://www.houstontx.gov/council/"}
    except Exception:
        pass
    return out
