"""Nearest USGS Harvey high-water marks (snapshot in data/hwm_harvey.json)."""
import json
import logging

from app import config
from app.services.data import haversine_m

log = logging.getLogger("hwm")
_snap: dict = {}
EVENT = "Harvey 2017"
URL = "https://stn.wim.usgs.gov/STNWeb/datadisplay/flooddata/#/"


def _load() -> dict:
    if not _snap:
        try:
            _snap.update(json.loads((config.DATA_DIR / "hwm_harvey.json").read_text()))
        except Exception as e:
            log.warning("hwm snapshot unreadable: %s", e)
            _snap.update({"marks": [], "snapshot_date": None})
    return _snap


def _wet(m) -> bool:
    h = m.get("h")
    return isinstance(h, (int, float)) and h > 0


def _note_code(h, mi):
    if not h or h <= 0:
        return "hwm.dry", {"mi": f"{mi:.1f}"}
    return "hwm.wet", {"h": f"{h:.1f}", "mi": f"{mi:.1f}"}


def _note(h: float, mi: float) -> str:
    d = f"{mi:.1f} mi away"
    if not h or h <= 0:
        return f"Water was at or below ground (0 ft) at a surveyed point {d} during Harvey. That does not mean your address stayed dry."
    return f"Water reached about {h:.1f} ft above ground at a surveyed point {d} during Harvey — not your exact address."


def nearby(lat: float, lon: float, radius_mi: float = 2.0, limit: int = 5) -> dict:
    snap = _load()
    out = []
    for m in snap.get("marks", []):
        if abs(m["lat"] - lat) > 0.5 or abs(m["lon"] - lon) > 0.5:
            continue
        mi = haversine_m(lat, lon, m["lat"], m["lon"]) / 1609.344
        if mi <= radius_mi:
            out.append((mi, m))
    out.sort(key=lambda t: t[0])
    marks = [{"id": m["id"], "distance_mi": round(mi, 2), "height_above_ground_ft": m["h"],
              "elevation_ft": m.get("elev"), "site_desc": m.get("desc"), "event": EVENT,
              "quality": m.get("q"), "survey_date": m.get("date"), "wet": _wet(m),
              "url": f"https://stn.wim.usgs.gov/STNServices/HWMs/{m['id']}.json",
              "note": _note(m["h"], mi), "note_code": _note_code(m["h"], mi)[0],
              "params": _note_code(m["h"], mi)[1]} for mi, m in out[:limit]]
    wet_n = sum(1 for _, m in out if _wet(m))
    first_wet = next(((mi, m) for mi, m in out if _wet(m)), None)
    if first_wet:
        mi, m = first_wet
        depth, ncode, nparams = m["h"], "hwm.near.wet", {"h": f"{m['h']:.1f}", "mi": f"{mi:.1f}"}
        note = f"Nearest surveyed high-water mark with water above ground: {m['h']:.1f} ft, {mi:.1f} mi away (Harvey). Not your exact address."
    elif out:
        ncode, nparams = "hwm.near.dry", {"r": f"{radius_mi:g}", "n": len(out)}
        depth, note = None, (f"No surveyed Harvey high-water mark with water above ground within {radius_mi:g} mi "
                             f"({len(out)} dry or depth-not-recorded). That does not mean the area stayed dry.")
    else:
        ncode, nparams = "hwm.near.none", {"r": f"{radius_mi:g}"}
        depth, note = None, f"No surveyed Harvey high-water mark within {radius_mi:g} mi. That does not mean the area stayed dry."
    return {"marks": marks, "nearest_depth_ft": depth, "nearest_note": note, "nearest_note_code": ncode, "nearest_note_params": nparams,
            "wet_marks": wet_n, "dry_marks": len(out) - wet_n,
            "source": "USGS Short-Term Network (STN), Harvey event 180",
            "snapshot_date": snap.get("snapshot_date")}
