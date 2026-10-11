"""WPC Excessive Rainfall outlook (Days 1-5) at a point."""
import asyncio

from app.services.codes import tag_warnings
from app.services.http import get_json

SOURCE = "https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer"
RANK = ["None", "Marginal", "Slight", "Moderate", "High"]


def _label(best: str) -> str:
    return "No excessive rainfall risk expected" if best == "None" else f"{best} risk of excessive rainfall"


async def _layer(day: int, lat: float, lon: float):
    d = await get_json(f"{SOURCE}/{day - 1}/query", {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": "outlook,valid_time", "returnGeometry": "false",
        "f": "json"}, ttl=600)
    if not isinstance(d, dict) or "features" not in d:
        return None
    best, vt = "None", None
    for f in d["features"]:
        a = f.get("attributes") or {}
        vt = vt or a.get("valid_time")
        text = (a.get("outlook") or "").lower()
        for c in RANK[1:]:
            if text.startswith(c.lower()) and RANK.index(c) > RANK.index(best):
                best = c
    return {"category": best, "valid_time": str(vt) if vt else None}


async def get_outlook(lat: float, lon: float, simulate: bool = False) -> dict:
    note = "WPC Excessive Rainfall Outlook, Days 1-5. Not official guidance for your address; check weather.gov."
    res = [None] * 5 if simulate else await asyncio.gather(*[_layer(i, lat, lon) for i in range(1, 6)])
    if simulate:
        sim = {1: "Slight", 2: "Moderate", 3: "Moderate", 4: "Marginal", 5: "None"}
        res = [{"category": sim[i], "valid_time": None} for i in range(1, 6)]
    days, warnings = [], []
    for i, r in enumerate(res, 1):
        if r is None:
            days.append({"day": i, "category": None, "label": None, "valid_time": None})
        else:
            days.append({"day": i, "category": r["category"], "label": _label(r["category"]), "valid_time": r["valid_time"]})
    if all(d["category"] is None for d in days):
        return tag_warnings({"day1": None, "days": days, "max_category": None, "prepare_nudge": False, "source": SOURCE,
                             "note": note, "note_code": "outlook.note",
                             "warnings": ["Rainfall outlook unavailable right now; check weather.gov"]})
    if any(d["category"] is None for d in days):
        warnings.append("Some rainfall outlook days are unavailable right now; check weather.gov")
    cats = [d["category"] for d in days if d["category"]]
    mx = max(cats, key=RANK.index)
    d1 = days[0]
    out = {"day1": {"category": d1["category"], "label": d1["label"], "valid_time": d1["valid_time"]} if d1["category"] else None,
           "days": days, "max_category": mx, "prepare_nudge": RANK.index(mx) >= RANK.index("Slight"),
           "source": SOURCE, "note": note, "note_code": "outlook.note"}
    if simulate:
        out["simulated"] = True
    if warnings:
        out["warnings"] = warnings
    return tag_warnings(out)
