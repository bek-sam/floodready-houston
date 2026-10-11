"""ArcGIS layer helper: full-layer GeoJSON cached 1h in memory + snapshot on disk."""
import time

from app.services import diskcache
from app.services.http import get_json

HCFCD = "https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services"
_mem: dict = {}


async def full_layer(name: str, url: str, ttl: float = 3600) -> list[dict]:
    """All features (GeoJSON) of a small layer. Falls back to the disk snapshot if ArcGIS is down."""
    hit = _mem.get(name)
    if hit and hit[0] > time.time():
        return hit[1]
    d = await get_json(url + "/query", {"where": "1=1", "outFields": "*", "f": "geojson", "outSR": 4326,
                                        "resultRecordCount": 2000}, ttl=0)
    feats = (d or {}).get("features") if isinstance(d, dict) else None
    if feats:
        _mem[name] = (time.time() + ttl, feats)
        diskcache.load("layers")[name] = feats
        diskcache.save("layers")
        return feats
    snap = diskcache.get("layers", name) or []
    if snap:
        _mem[name] = (time.time() + 300, snap)
    return snap
