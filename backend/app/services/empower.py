"""HHS emPOWER counts of Medicare beneficiaries who rely on power-dependent devices, by ZIP (no key)."""
import re

from app.services.http import get_json

URL = ("https://services2.arcgis.com/ZQ4jTQn6k7VPXEwO/arcgis/rest/services/"
       "HHS_emPOWER_REST_Service_Public/FeatureServer/1/query")
SOURCE = "https://catalog.data.gov/dataset/hhs_empower_rest_service_public"
TTL = 7 * 24 * 3600


def valid_zip(z: str) -> bool:
    return bool(re.fullmatch(r"\d{5}", z or ""))


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


async def get_empower(zip_code: str) -> dict:
    out = {"zip": zip_code, "medicare_benes": None, "power_dependent_devices": None, "oxygen": None,
           "dialysis": None, "available": False, "source": SOURCE,
           "map": "https://empowerprogram.hhs.gov/empowermap",
           "note": "Medicare beneficiaries only. Counts for the ZIP, not individuals' locations.",
           "puc": {"url": "https://www.ercot.com/files/docs/2024/01/17/PUC-Critical-Care-Form.pdf",
                   "note": "Critical care designation does not guarantee uninterrupted power or faster restoration."},
           "co": {"url": "https://www.cdc.gov/carbon-monoxide/about/index.html"}}
    d = await get_json(URL, {
        "where": f"Zip_Code='{zip_code}'",
        "outFields": "Zip_Code,Medicare_Benes,Power_Dependent_Devices_DME,O2_Services_Any_DME,Facility_ESRD_Dialysis_Any_DME",
        "returnGeometry": "false", "f": "json"}, ttl=TTL)
    feats = d.get("features") if isinstance(d, dict) else None
    if feats:
        a = (feats[0] or {}).get("attributes") or {}
        out.update(medicare_benes=_int(a.get("Medicare_Benes")),
                   power_dependent_devices=_int(a.get("Power_Dependent_Devices_DME")),
                   oxygen=_int(a.get("O2_Services_Any_DME")),
                   dialysis=_int(a.get("Facility_ESRD_Dialysis_Any_DME")), available=True)
    else:
        out["warnings"] = ["emPOWER data unavailable for this ZIP right now"]
    return out
