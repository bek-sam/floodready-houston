"""Shelter directory from the public ArcGIS Evacuation_Shelters layer (snapshot fallback)."""
from app.services import arcgis
from app.services.codes import tag_warnings
from app.services.data import haversine_m, load_json

SOURCE = "https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Evacuation_Shelters/FeatureServer/0"
# Coded-value domain read from the layer metadata (ShelterStatus); anything else is "Unknown" (never open).
STATUS = {0: "Pending", 1: "Open", 2: "Full", 3: "Closed"}
# Record CreationDate/EditDate in the layer are Aug-Sep 2017 (Harvey); layer last edited Jan 2019. Not live data.
HISTORICAL = True
DATA_AS_OF = "2017 (Hurricane Harvey)"
NOTE = ("These are sites the City used as shelters during Hurricane Harvey (2017) \u2014 NOT live status. "
        "During a storm, call 311 or 211, or check houstonoem.org for shelters open now.")


def _shelter(f: dict, lat: float, lon: float) -> dict | None:
    try:
        x, y = f["geometry"]["coordinates"][:2]
        p = f.get("properties") or {}
        st = p.get("ShelterStatus")
        status = st if isinstance(st, str) and st in STATUS.values() else STATUS.get(st, "Unknown")
        return {"name": p.get("Name"), "address": p.get("Address"), "county": p.get("County"), "status_2017": status,
                "capacity": p.get("Capacity"), "occupancy": p.get("Occupancy"),
                "pet_friendly": p.get("PetFriendly") == 0, "lat": y, "lon": x,
                "distance_mi": round(haversine_m(lat, lon, y, x) / 1609.34, 1)}
    except Exception:
        return None


async def get_shelters(lat: float, lon: float, pet_friendly: bool = False, limit: int = 5) -> dict:
    warnings = []
    feats = await arcgis.full_layer("shelters", SOURCE)
    if not feats:
        snap = load_json("shelters.json", {}) or {}
        feats = snap.get("features", []) if isinstance(snap, dict) else []
        warnings.append("Live shelter data unavailable; showing an older snapshot. Call 211 to confirm." if feats
                        else "Shelter data unavailable right now. Call 211 or 311.")
    items = [s for s in (_shelter(f, lat, lon) for f in feats) if s]
    if pet_friendly:
        items = [s for s in items if s["pet_friendly"]]
    items.sort(key=lambda s: s["distance_mi"])
    out = {"shelters": items[:max(limit, 0)], "any_open": False, "historical": HISTORICAL,
           "data_as_of": DATA_AS_OF, "source": SOURCE, "note": NOTE, "note_code": "shelters.note"}
    if warnings:
        out["warnings"] = warnings
        tag_warnings(out)
    return out
