"""Flood risk at a point: FEMA zone + elevation + nearest live gauges + heuristics."""
import asyncio

from app import freshness
from app.services.harvey import harvey_at
from app.services.codes import tag_warnings
from app.services.gauges import nearest_gauges
from app.services.http import get_json

NFHL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
OPEN_METEO_ELEV = "https://api.open-meteo.com/v1/elevation"
EPQS = "https://epqs.nationalmap.gov/v1/json"
CENSUS_GEO = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

CITY_LIMITS = "https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services/City_Limit_Boundaries_FL/FeatureServer/0/query"
BARKER = "https://gisportal.fortbendcountytx.gov/arcgis/rest/services/Hosted/Barker_Reservoir_Inundation_Map/FeatureServer/2/query"  # 107 ft pool
# Approximate bounding box (lat_min, lat_max, lon_min, lon_max) of the Addicks pool. Rough, awareness only.
ADDICKS_BOX = (29.77, 29.84, -95.69, -95.60)
LOW_GROUND_MARGIN_FT = 5.0

SRC_HARVEY = "https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county"
SRC_FLAT = "https://maapnext.harriscountytx.gov/Understand-Your-Risk"
HARVEY_OUTSIDE_NOTE = ("The City of Houston's Harvey flood map doesn't fully cover this city \u2014 no Harvey extent data here. "
                       "Absence from it is not evidence this place stayed dry.")
SRC_DAMS = "https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/"
SRC_MAPS = "https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/"
SRC_RICE = "https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk"


def in_addicks_box(lat: float, lon: float) -> bool:
    a, b, c, d = ADDICKS_BOX
    return a <= lat <= b and c <= lon <= d


async def reservoir_status(lat: float, lon: float) -> dict:
    """Barker: Fort Bend inundation polygon (point query). Addicks: approximate box."""
    d = await get_json(BARKER, {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "returnCountOnly": "true", "f": "json"}, ttl=3600)
    barker = (d or {}).get("count", 0) > 0 if isinstance(d, dict) else False
    addicks = in_addicks_box(lat, lon)
    note, code = "Barker: Fort Bend County inundation map (107 ft pool). Addicks: approximate area only.", "res.note"
    if d is None:
        note, code = "Barker inundation service unavailable. Addicks: approximate area only.", "res.noteDown"
    return {"in_area": barker or addicks, "barker": barker, "addicks_approx": addicks, "note": note, "note_code": code}


def _low_ground(elev, gauges):
    """Compare ground elevation with the minor-flood ELEVATION of the nearest gauge that has a known datum.
    Needs gauge['datum_ft'] (ft above sea level). Returns (value, note); None if no datum is available."""
    if elev is None:
        return None, "Elevation unavailable", "lg.noelev", {}
    for g in gauges:
        datum, minor = g.get("datum_ft"), (g.get("flood_stages") or {}).get("minor")
        if datum is not None and minor is not None:
            return (elev <= datum + minor + LOW_GROUND_MARGIN_FT, f"Compared with {g['name']} minor flood stage elevation ({datum + minor:.0f} ft)",
                    "lg.compare", {"name": g["name"], "ft": f"{datum + minor:.0f}"})
    return None, "Unknown: no gauge datum available to compare ground elevation with flood-stage elevation", "lg.nodatum", {}


def build_facts(zone, sfha, reservoir) -> list[dict]:
    facts = []
    if zone and not sfha:
        facts.append({"text": f"Zone {zone} is outside the mapped high-risk floodplain, but nearly half of Harvey-flooded homes in Harris County were outside the 100- and 500-year floodplains.", "source": SRC_HARVEY, "code": "fact.zoneOut", "params": {"zone": zone}})
    elif sfha:
        facts.append({"text": "This location is in a FEMA Special Flood Hazard Area; flood insurance is typically required with a federally backed mortgage.", "source": SRC_MAPS, "code": "fact.sfha", "params": {}})
    facts.append({"text": "Harvey flooded 154,170 Harris County homes and only 36% were insured.", "source": SRC_HARVEY, "code": "fact.harveyIns", "params": {}})
    facts.append({"text": "Flat, clay-soil terrain means you don't have to live near a bayou to flood.", "source": SRC_FLAT, "code": "fact.flat", "params": {}})
    facts.append({"text": "Draft FEMA maps use rainfall rates more than 30% higher than the 2007 maps still in effect.", "source": SRC_MAPS, "code": "fact.maps", "params": {}})
    if reservoir:
        facts.append({"text": "You are near the Addicks/Barker reservoirs (1940s dams rated extremely high risk); Harvey releases flooded homes downstream.", "source": SRC_DAMS, "code": "fact.dams", "params": {}})
    return facts


async def _fema(lat, lon):
    return await get_json(NFHL, {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
        "returnGeometry": "false", "f": "json"}, ttl=3600)


async def _elev(lat, lon):
    return await get_json(EPQS, {"x": lon, "y": lat, "units": "Feet", "wkid": 4326}, ttl=3600)


async def _juris(lat, lon):
    return await get_json(CITY_LIMITS, {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                        "spatialRel": "esriSpatialRelIntersects", "outFields": "NAME,SERVICE_TY",
                                        "returnGeometry": "false", "f": "json"}, ttl=3600)


def harvey_for_jurisdiction(hv: dict, jur: str) -> dict:
    """The layer is the City of Houston's own estimate: a miss in another city is "no data", not "dry". A hit stays true."""
    if hv.get("flooded") is False and jur != "Unknown" and not jur.startswith("City of Houston"):
        return {**hv, "flooded": None, "note": HARVEY_OUTSIDE_NOTE, "note_code": "harvey.outside"}
    return hv


def jurisdiction_name(juris) -> str:
    try:
        feats = juris["features"]
        full = [f["attributes"] for f in feats if f["attributes"].get("SERVICE_TY") == "FULL"]
        if full:
            return f"City of {full[0]['NAME'].title()}"
        if feats:
            return f"{feats[0]['attributes']['NAME'].title()} (limited purpose area)"
        return "Unincorporated (county)"
    except Exception:
        return "Unknown"


async def get_risk(lat: float, lon: float, simulate: bool = False) -> dict:
    fema, elev, juris, gauges = await asyncio.gather(
        _fema(lat, lon), _elev(lat, lon), _juris(lat, lon), nearest_gauges(lat, lon, 3, simulate),
        return_exceptions=True)
    warnings = []
    zone = subtype = None
    sfha = None
    try:
        a = fema["features"][0]["attributes"]
        zone, subtype = a.get("FLD_ZONE"), a.get("ZONE_SUBTY")
        sfha = a.get("SFHA_TF") == "T"
    except Exception:
        warnings.append("FEMA flood zone unavailable (service down or no mapped data at this point)")
    elevation = None
    elev_source = None
    try:
        v = float(elev["value"])
        if v > -1000:
            elevation, elev_source = round(v, 1), "usgs_epqs"
    except Exception:
        pass
    if elevation is None:
        try:
            om = await get_json(OPEN_METEO_ELEV, {"latitude": lat, "longitude": lon}, ttl=3600)
            elevation = round(float(om["elevation"][0]) * 3.28084, 1)
            elev_source = "open_meteo_approx"
            warnings.append("USGS elevation unavailable; using approximate Open-Meteo elevation")
        except Exception:
            warnings.append("Elevation unavailable")
    if isinstance(gauges, Exception) or gauges is None:
        gauges, _ = [], warnings.append("Gauge data unavailable")
    elif not gauges:
        warnings.append("No gauge data file found")
    jur, jur_code, jur_params = "Unknown", "jur.unknown", {}
    try:
        feats = juris["features"]
        full = [f["attributes"] for f in feats if f["attributes"].get("SERVICE_TY") == "FULL"]
        if full:
            jur = f"City of {full[0]['NAME'].title()}"
            jur_code, jur_params = "jur.city", {"name": full[0]["NAME"].title()}
        elif feats:
            jur = f"{feats[0]['attributes']['NAME'].title()} (limited purpose area)"
            jur_code, jur_params = "jur.limited", {"name": feats[0]["attributes"]["NAME"].title()}
        else:
            jur, jur_code = "Unincorporated (county)", "jur.uninc"
    except Exception:
        warnings.append("Jurisdiction lookup failed")
    rs = await reservoir_status(lat, lon)
    reservoir = rs["in_area"]
    low, low_note, low_code, low_params = _low_ground(elevation, gauges)
    hv = harvey_for_jurisdiction(harvey_at(lat, lon), jur)
    out = {"fema_zone": zone, "zone_subtype": subtype, "sfha": sfha, "elevation_ft": elevation, "elevation_source": elev_source,
           "low_ground": low, "low_ground_note": low_note, "low_ground_note_code": low_code, "low_ground_note_params": low_params, "nearest_gauges": gauges,
           "reservoir_area": reservoir, "harvey": hv, "jurisdiction": jur, "jurisdiction_code": jur_code, "jurisdiction_params": jur_params, "facts": build_facts(zone, sfha, reservoir)}
    if warnings:
        out["warnings"] = warnings
        tag_warnings(out)
    gl = [g for g in gauges if isinstance(g, dict)]
    storm = any(g.get("status") in ("action", "minor", "moderate", "major") for g in gl)
    obs = [g["observed_at"] for g in gl if g.get("observed_at") and g["observed_at"] != "simulated"]
    out["meta"] = freshness.meta("FEMA NFHL + USGS EPQS + NOAA NWPS", "live", as_of=max(obs) if obs else None,
                                 storm=storm or freshness.storm_on())
    out["harvey"] = {**out["harvey"], "as_of": "2017-08-31", "freshness": "historical"}
    return out
