"""HCFCD buyout areas (non-PII point layer HCFCD_Buyout_Areas). Never touches the Voluntary Buyout Assistance layer."""
import time

from app.services import diskcache
from app.services.arcgis import HCFCD
from app.services.data import haversine_m
from app.services.http import get_json

URL = f"{HCFCD}/HCFCD_Buyout_Areas/FeatureServer/0/query"
SOURCE = "https://www.hcfcd.org/Flood-Risk-Reduction/Buyout-Program"
RADIUS_MI = 0.5
TTL = 24 * 3600
_mem: dict = {}


async def _areas() -> list[dict] | None:
    if _mem.get("t", 0) > time.time():
        return _mem["v"]
    d = await get_json(URL, {"where": "1=1", "outFields": "Area_Name,Jurisd", "outSR": 4326, "f": "geojson",
                             "resultRecordCount": 2000}, ttl=0)
    feats = (d or {}).get("features") if isinstance(d, dict) else None
    if feats:
        rows = []
        for f in feats:
            try:
                x, y = f["geometry"]["coordinates"][:2]
                rows.append({"name": f["properties"].get("Area_Name"), "lat": y, "lon": x})
            except Exception:
                continue
        _mem.update(t=time.time() + TTL, v=rows)
        diskcache.put("buyout_areas", "all", rows)
        return rows
    return diskcache.get("buyout_areas", "all")


async def buyout_area(lat: float, lon: float) -> dict:
    rows = await _areas()
    if not rows:
        return {"in_buyout_area": None, "area_name": None, "source": SOURCE,
                "note": "Buyout area data is unavailable right now. Unknown, not a 'no'.", "note_code": "buyout.unavail", "params": {}}
    best, mi = None, 1e9
    for r in rows:
        m = haversine_m(lat, lon, r["lat"], r["lon"]) / 1609.34
        if m < mi:
            best, mi = r, m
    if best and mi <= RADIUS_MI:
        return {"in_buyout_area": True, "area_name": best["name"], "source": SOURCE,
                "note": f"Within {RADIUS_MI} mi of an HCFCD buyout area ({best['name']}). Buyouts are voluntary; contact HCFCD to ask about eligibility.",
                "note_code": "buyout.in", "params": {"r": RADIUS_MI, "name": best["name"]}}
    return {"in_buyout_area": False, "area_name": None, "source": SOURCE,
            "note": f"No HCFCD buyout area within {RADIUS_MI} mi (area layer is point-based, so this is approximate).",
            "note_code": "buyout.out", "params": {"r": RADIUS_MI}}
