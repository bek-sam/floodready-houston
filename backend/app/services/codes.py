"""Stable i18n codes for backend-authored strings. The English text stays in the API (backward compatible);
clients render t(code, params) when they have the key and fall back to the English text otherwise."""
import re

WARN = {
    "FEMA flood zone unavailable (service down or no mapped data at this point)": "w.fema",
    "USGS elevation unavailable; using approximate Open-Meteo elevation": "w.elevApprox",
    "Elevation unavailable": "w.elev",
    "Gauge data unavailable": "w.gauge",
    "No gauge data file found": "w.gaugeFile",
    "Jurisdiction lookup failed": "w.juris",
    "Routing service unavailable; showing a straight line, not a real route": "w.route",
    "NWS alerts unavailable right now; check weather.gov": "w.nws",
    "civic data file not available yet": "w.civicFile",
    "No HCFCD bond projects within 5 miles (or layer unavailable)": "w.bond",
    "Live shelter data unavailable; showing an older snapshot. Call 211 to confirm.": "w.shelterOld",
    "Shelter data unavailable right now. Call 211 or 311.": "w.shelter",
    "Rainfall outlook unavailable right now; check weather.gov": "w.outlook",
    "OpenFEMA unavailable; showing a saved snapshot": "w.zipSnap",
    "OpenFEMA unavailable; no claims data. Zero here means unknown, not safe.": "w.zipNone",
}


def tag_warnings(out: dict) -> dict:
    """Adds warning_codes aligned by index with warnings (empty string = no code)."""
    w = out.get("warnings") if isinstance(out, dict) else None
    if isinstance(w, list) and w:
        out["warning_codes"] = [WARN.get(x, "") for x in w]
    return out


_HWM = re.compile(r"USGS surveyed a Hurricane Harvey \(2017\) high-water mark at this road crossing(?:, ([\d.]+) ft above ground)? \((.*)\)")
_PREFIX = [
    ("Low crossings and bridge approaches flood first", "route.r.low"),
    ("Drivers drown in flooded underpasses", "route.r.drown"),
    ("Listed by City of Houston officials", "route.r.listed"),
    ("City of Houston flood signal location", "route.r.signal"),
    ("City officials say this intersection", "route.r.barricade"),
    ("OpenStreetMap road underpass/tunnel", "route.r.osm"),
    ("Known flood-prone crossing", "route.r.known"),
]


def reason_code(text: str | None) -> tuple[str, dict] | None:
    if not text:
        return None
    m = _HWM.match(text)
    if m:
        return ("route.r.hwmFt", {"ft": m.group(1), "water": m.group(2)}) if m.group(1) else ("route.r.hwm", {"water": m.group(2)})
    for p, c in _PREFIX:
        if text.startswith(p):
            return c, {}
    return None
