import asyncio
import time

from app.services.codes import tag_warnings
from app.services.arcgis import HCFCD, full_layer
from app.services.data import haversine_m, load_json
from app.services.officials import get_officials
from app.services.risk import reservoir_status

BOND_URL = f"{HCFCD}/Bond_CIP_Structural_CJO/FeatureServer/0"
BOND_SOURCE = "https://www.hcfcd.org/bond-program"
MAX_MI, TOP_N = 5.0, 10


async def bond_projects(lat: float, lon: float) -> list[dict]:
    out = []
    for f in await full_layer("bond_cip", BOND_URL):
        try:
            x, y = f["geometry"]["coordinates"][:2]
            p = f["properties"]
        except Exception:
            continue
        mi = haversine_m(lat, lon, y, x) / 1609.34
        if mi <= MAX_MI:
            out.append({"name": p.get("Project_Title"), "status": p.get("Status"), "budgeted": p.get("Budgeted"),
                        "spent": p.get("Spent"), "distance_mi": round(mi, 1), "url": p.get("Hyperlink") or BOND_SOURCE})
    return sorted(out, key=lambda r: r["distance_mi"])[:TOP_N]


_cache: dict = {}
_inflight: dict = {}
CACHE_TTL = 3600


async def get_civic(lat: float, lon: float) -> dict:
    """Cached 1 h per (lat,lon) at 3 dp; concurrent identical requests share one computation."""
    key = (round(lat, 3), round(lon, 3))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    task = _inflight.get(key)
    if task is None:
        task = asyncio.ensure_future(_build_civic(lat, lon))
        _inflight[key] = task
        task.add_done_callback(lambda _t: _inflight.pop(key, None))
    out = await asyncio.shield(task)
    off = out.get("officials") or {}
    if off.get("commissioner") or off.get("floodplain_admin"):
        _cache[key] = (time.time(), out)
    return out


async def _build_civic(lat: float, lon: float) -> dict:
    d = load_json("civic.json", None)
    warnings = []
    if not isinstance(d, dict):
        d = {}
        warnings.append("civic data file not available yet")
    bond = dict(d.get("bond") or {})
    bond["facts"] = [{**f, "code": f.get("code") or f"civic.bond.{i}", "params": {}} for i, f in enumerate(bond.get("facts") or [])]
    async def _t(c, default):
        try:
            return await asyncio.wait_for(c, 6)
        except Exception:
            return default

    projects, rs, officials = await asyncio.gather(
        _t(bond_projects(lat, lon), []),
        _t(reservoir_status(lat, lon), {"in_area": None, "note": "Reservoir lookup timed out", "note_code": "civic.res.timeout"}),
        get_officials(lat, lon))
    bond["projects"] = projects
    if not bond["projects"]:
        warnings.append("No HCFCD bond projects within 5 miles (or layer unavailable)")
    reservoir = dict(d.get("reservoir") or {})
    reservoir["in_area"] = rs["in_area"]
    reservoir["note"] = rs["note"]
    reservoir["note_code"] = rs["note_code"]
    reservoir["facts"] = [{**f, "code": f.get("code") or f"civic.res.{i}", "params": {}} for i, f in enumerate(reservoir.get("facts") or [])]
    out = {"bond": bond, "reservoir": reservoir, "responsibility": [{**r, "code": f"civic.resp.{i}"} for i, r in enumerate(d.get("responsibility") or [])],
           "officials": officials}
    if warnings:
        out["warnings"] = warnings
        tag_warnings(out)
    return out
