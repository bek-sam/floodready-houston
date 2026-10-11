"""Hurricane evacuation zone (Harris County GIS ZIP-Zones) + NHC storm-surge risk at a point.

Both layers are static planning data: cached 24 h in memory and snapshotted to disk. A failed call
never reads as "safe": fields come back null with status "unavailable" (or the last disk snapshot, flagged stale)."""
import asyncio
import re
import time

from app.services import diskcache
from app.services.http import get_json

ZONE_URL = "https://services.arcgis.com/su8ic9KbA7PYVxPS/arcgis/rest/services/HurricaneEvac_Zones/FeatureServer/0/query"
SURGE_URL = "https://mapservices.weather.noaa.gov/tropical/rest/services/tropical/StormSurgeRisk/MapServer/identify"
SURGE_LAYERS = {"cat1": 5, "cat2": 9, "cat3": 13, "cat4": 17, "cat5": 21}
TTL = 24 * 3600
SNAP = "evac"
_mem: dict = {}

GUIDANCE = "Follow official evacuation orders from your local officials (Harris County / your city). This is not an order."
SURGE_NOTE = ("NHC storm-surge risk maps are worst-case SLOSH scenarios for hurricanes only, not a forecast, "
              "and they do not show rain or bayou flooding.")


def _key(lat: float, lon: float) -> str:
    return f"{lat:.3f},{lon:.3f}"


async def _zone(lat, lon):
    d = await get_json(ZONE_URL, {"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
                                  "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
                                  "outFields": "Zone,Zip5digit,Name,County", "returnGeometry": "false"}, ttl=TTL)
    if not isinstance(d, dict) or "features" not in d:
        return "error", None
    feats = d["features"]
    return ("ok", feats[0].get("attributes") or {}) if feats else ("ok", None)


async def _surge_layer(lat, lon, layer):
    p = {"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "sr": 4326,
         "layers": f"all:{layer}", "tolerance": 1, "returnGeometry": "false",
         "mapExtent": f"{lon - .01},{lat - .01},{lon + .01},{lat + .01}", "imageDisplay": "400,400,96"}
    d = await get_json(SURGE_URL, p, ttl=TTL)
    if not isinstance(d, dict) or "results" not in d:
        return "error", None
    for r in d["results"]:
        a = r.get("attributes") or {}
        cn = a.get("Raster.ClassName")
        if cn and str(cn).lower() not in ("nodata", "null", ""):
            return "ok", str(cn)
    return "ok", None


def _zone_letter(raw: str | None):
    if not raw:
        return None
    m = re.search(r"zone\s+([A-Za-z]+)\s*$", raw.strip(), re.I)
    return (m.group(1).upper() if len(m.group(1)) == 1 else m.group(1).title()) if m else raw.strip()


def _range(txt):
    """NHC class text -> {min_ft, max_ft|null, label}; open-ended ranges have max_ft null and a "N+ ft" label."""
    if not txt:
        return None
    t = str(txt).lower()
    m = re.search(r"(\d+)", t)
    n = int(m.group(1)) if m else None
    if n is None:
        return {"min_ft": None, "max_ft": None, "label": str(txt)}
    if re.search(r"greater|more|over", t):
        return {"min_ft": n, "max_ft": None, "label": f"{n}+ ft"}
    if re.search(r"less|under|below", t):
        return {"min_ft": 0, "max_ft": n, "label": f"under {n} ft"}
    r = re.findall(r"\d+", t)
    if len(r) >= 2:
        return {"min_ft": int(r[0]), "max_ft": int(r[1]), "label": f"{r[0]}-{r[1]} ft"}
    return {"min_ft": n, "max_ft": n, "label": f"{n} ft"}


def _build(zst, zattrs, sres) -> dict:
    surge_ok = all(s == "ok" for s, _ in sres.values())
    surge = {k: (v if s == "ok" else None) for k, (s, v) in sres.items()}
    in_surge = any(v for v in surge.values())
    zone = _zone_letter((zattrs or {}).get("Zone"))
    notes = []
    if zst == "error":
        notes.append("Evacuation-zone lookup unavailable right now; this is not a sign you are outside a zone.")
    elif zone is None:
        notes.append("No Harris-area hurricane evacuation zone found at this point (outside coverage or not in a zone). "
                     "Check your county's evacuation map.")
    if not surge_ok:
        notes.append("Storm-surge lookup unavailable right now; this is not a sign of no surge risk.")
    elif not in_surge:
        notes.append("No NHC storm-surge inundation mapped here. Rain and bayou flooding can still happen.")
    return {
        "zone": zone,
        "zone_label": (zattrs or {}).get("Zone"),
        "zip": (zattrs or {}).get("Zip5digit"),
        "area": (zattrs or {}).get("Name"),
        "county": (zattrs or {}).get("County"),
        "zone_status": "unavailable" if zst == "error" else ("in_zone" if zone else "not_in_zone"),
        "surge": surge,
        "surge_ranges": {k: _range(v) for k, v in surge.items()},
        "surge_status": "unavailable" if not surge_ok else ("mapped" if in_surge else "none"),
        "guidance": GUIDANCE,
        "surge_note": SURGE_NOTE,
        "notes": notes,
        "links": {"readyharris": "https://www.readyharris.org/", "hurricanes": "https://www.ready.gov/hurricanes"},
        "sources": ["Harris County GIS HurricaneEvac_Zones", "NOAA NHC National Storm Surge Risk Maps"],
    }


async def evac_at(lat: float, lon: float) -> dict:
    """Returns the result dict plus '_stale' (bool) and '_as_of' (epoch seconds)."""
    k = _key(lat, lon)
    hit = _mem.get(k)
    if hit and time.time() - hit["t"] < TTL:
        return {**hit["v"], "_stale": False, "_as_of": hit["t"]}
    (zst, zattrs), *layers = await asyncio.gather(
        _zone(lat, lon), *[_surge_layer(lat, lon, n) for n in SURGE_LAYERS.values()])
    sres = dict(zip(SURGE_LAYERS, layers))
    out = _build(zst, zattrs, sres)
    failed = zst == "error" or any(s == "error" for s, _ in sres.values())
    if not failed:
        _mem[k] = {"t": time.time(), "v": out}
        diskcache.put(SNAP, k, {"t": time.time(), "v": out})
        return {**out, "_stale": False, "_as_of": time.time()}
    snap = diskcache.get(SNAP, k)
    if snap and snap.get("v"):
        return {**snap["v"], "_stale": True, "_as_of": snap.get("t")}
    return {**out, "_stale": True, "_as_of": None}
