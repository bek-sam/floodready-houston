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


def _note(h: float, mi: float) -> str:
    d = f"{mi:.1f} mi away"
    if h <= 0:
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
              "quality": m.get("q"), "survey_date": m.get("date"),
              "url": f"https://stn.wim.usgs.gov/STNServices/HWMs/{m['id']}.json",
              "note": _note(m["h"], mi)} for mi, m in out[:limit]]
    return {"marks": marks, "nearest_depth_ft": marks[0]["height_above_ground_ft"] if marks else None,
            "nearest_note": marks[0]["note"] if marks else f"No surveyed Harvey high-water mark within {radius_mi:g} mi. That does not mean the area stayed dry.",
            "source": "USGS Short-Term Network (STN), Harvey event 180",
            "snapshot_date": snap.get("snapshot_date")}
