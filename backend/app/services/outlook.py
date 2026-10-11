"""WPC Excessive Rainfall Day 1 outlook at a point."""
from app.services.codes import tag_warnings
from app.services.http import get_json

SOURCE = "https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer"
LAYER = 0  # "Excessive Rainfall Day 1"
RANK = ["None", "Marginal", "Slight", "Moderate", "High"]


async def get_outlook(lat: float, lon: float) -> dict:
    d = await get_json(f"{SOURCE}/{LAYER}/query", {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": "outlook", "returnGeometry": "false", "f": "json"}, ttl=600)
    note = "WPC Excessive Rainfall Outlook, Day 1. Not official guidance for your address; check weather.gov."
    if not isinstance(d, dict) or "features" not in d:
        return tag_warnings({"day1": None, "source": SOURCE, "note": note, "note_code": "outlook.note",
                             "warnings": ["Rainfall outlook unavailable right now; check weather.gov"]})
    best = "None"
    for f in d["features"]:
        text = ((f.get("attributes") or {}).get("outlook") or "").lower()
        for c in RANK[1:]:
            if text.startswith(c.lower()) and RANK.index(c) > RANK.index(best):
                best = c
    label = "No excessive rainfall risk expected" if best == "None" else f"{best} risk of excessive rainfall"
    return {"day1": {"category": best, "label": label}, "source": SOURCE, "note": note, "note_code": "outlook.note"}
