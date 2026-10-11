from fastapi import APIRouter

from app import freshness
from app.services.codes import reason_code
from app.services.data import load_json

router = APIRouter()


@router.get("/crossings")
async def crossings():
    d = load_json("crossings.geojson")
    d = d if isinstance(d, dict) else {"type": "FeatureCollection", "features": []}
    for f in d.get("features", []):
        pr = f.get("properties") if isinstance(f, dict) else None
        if isinstance(pr, dict) and isinstance(pr.get("reasons"), list):
            pr["reason_codes"] = [dict(zip(("code", "params"), reason_code(r))) if reason_code(r) else None for r in pr["reasons"]]
    return {**d, "meta": freshness.snap_meta("crossings", "https://github.com/ (curated from sourced crossings data; see feature sources)")}
