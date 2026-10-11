"""Defensive loaders for data-agent files."""
import json
import logging
import math

from app.config import DATA_DIR

log = logging.getLogger("data")


def load_json(rel: str, default=None):
    try:
        return json.loads((DATA_DIR / rel).read_text())
    except Exception as e:
        log.warning("data file %s unavailable: %s", rel, e)
        return default


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
