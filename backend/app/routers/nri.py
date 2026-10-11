from fastapi import APIRouter

from app import freshness
from app.services.nri import get_nri

router = APIRouter()


@router.get("/nri")
async def nri(lat: float, lon: float):
    out = await get_nri(lat, lon)
    return freshness.with_meta(out, source="FEMA National Risk Index", freshness="recent")
