from fastapi import APIRouter

from app.services.risk import get_risk

router = APIRouter()


@router.get("/risk")
async def risk(lat: float, lon: float, simulate: str | None = None):
    return await get_risk(lat, lon, simulate=(simulate == "storm"))
