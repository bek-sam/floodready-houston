from fastapi import APIRouter

from app import freshness
from app.services.buyouts import buyout_area

router = APIRouter()


@router.get("/buyout-area")
async def get_buyout_area(lat: float, lon: float):
    out = await buyout_area(lat, lon)
    return freshness.with_meta(out, source=out.get("source", "Harris County Flood Control") if isinstance(out, dict) else "", freshness="cached", storm=False)
