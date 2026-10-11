"""FEMA National Risk Index (census tract) at a point."""
from app.services.http import get_json

URL = "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Census_Tracts/FeatureServer/0/query"
SOURCE = "https://hazards.fema.gov/nri/"
FIELDS = "TRACTFIPS,IFLD_RISKR,IFLD_EALR,IFLD_AFREQ,RESL_RATNG,SOVI_RATNG,RISK_RATNG,POPULATION"
NOTE = "Statistical index for the census tract, not your house."


async def get_nri(lat: float, lon: float) -> dict:
    d = await get_json(URL, {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                             "spatialRel": "esriSpatialRelIntersects", "outFields": FIELDS,
                             "returnGeometry": "false", "f": "json"}, ttl=86400)
    if not isinstance(d, dict) or not isinstance(d.get("features"), list):
        return {"available": False, "source": SOURCE, "warnings": ["FEMA National Risk Index unavailable right now"]}
    if not d["features"]:
        return {"available": False, "source": SOURCE,
                "warnings": ["No National Risk Index data for this location (US census tracts only)"]}
    a = d["features"][0].get("attributes") or {}
    return {"available": True, "tract": a.get("TRACTFIPS"),
            "inland_flood": {"rating": a.get("IFLD_RISKR"), "annual_freq_events": a.get("IFLD_AFREQ")},
            "expected_loss_rating": a.get("IFLD_EALR"),
            "resilience": {"rating": a.get("RESL_RATNG")},
            "social_vulnerability": {"rating": a.get("SOVI_RATNG")},
            "overall_risk": {"rating": a.get("RISK_RATNG")},
            "population": a.get("POPULATION"), "source": SOURCE, "note": NOTE}
