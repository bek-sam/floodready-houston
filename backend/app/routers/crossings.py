from fastapi import APIRouter

from app import freshness
from app.services.data import load_json

router = APIRouter()


@router.get("/crossings")
async def crossings():
    d = load_json("crossings.geojson")
    d = d if isinstance(d, dict) else {"type": "FeatureCollection", "features": []}
    return {**d, "meta": freshness.snap_meta("crossings", "https://github.com/ (curated from sourced crossings data; see feature sources)")}
