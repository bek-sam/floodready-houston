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


async def get_civic(lat: float, lon: float) -> dict:
    d = load_json("civic.json", None)
    warnings = []
    if not isinstance(d, dict):
        d = {}
        warnings.append("civic data file not available yet")
    bond = dict(d.get("bond") or {})
    bond["facts"] = [{**f, "code": f"civic.bond.{i}", "params": {}} for i, f in enumerate(bond.get("facts") or [])]
    bond["projects"] = await bond_projects(lat, lon)
    if not bond["projects"]:
        warnings.append("No HCFCD bond projects within 5 miles (or layer unavailable)")
    reservoir = dict(d.get("reservoir") or {})
    rs = await reservoir_status(lat, lon)
    reservoir["in_area"] = rs["in_area"]
    reservoir["note"] = rs["note"]
    reservoir["note_code"] = rs["note_code"]
    reservoir["facts"] = [{**f, "code": f"civic.res.{i}", "params": {}} for i, f in enumerate(reservoir.get("facts") or [])]
    out = {"bond": bond, "reservoir": reservoir, "responsibility": [{**r, "code": f"civic.resp.{i}"} for i, r in enumerate(d.get("responsibility") or [])],
           "officials": await get_officials(lat, lon)}
    if warnings:
        out["warnings"] = warnings
        tag_warnings(out)
    return out
