from fastapi import APIRouter

from app import freshness
from app.services.outlook import get_outlook

router = APIRouter()


@router.get("/outlook")
async def outlook(lat: float, lon: float):
    out = await get_outlook(lat, lon)
    return freshness.with_meta(out, source=out.get("source", "NOAA WPC") if isinstance(out, dict) else "", freshness="recent")
