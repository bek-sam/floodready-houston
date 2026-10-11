from fastapi import APIRouter

from app import freshness
from app.services.civic import get_civic

router = APIRouter()


@router.get("/civic")
async def civic(lat: float, lon: float):
    out = await get_civic(lat, lon)
    if isinstance(out, dict):
        out["meta"] = freshness.snap_meta("civic", "data/civic.json (sourced facts) + ArcGIS officials layers")
    return out
