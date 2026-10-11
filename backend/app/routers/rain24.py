from fastapi import APIRouter

from app.services.rain24 import get_rain24

router = APIRouter()


@router.get("/rain24")
async def rain24(lat: float, lon: float):
    return await get_rain24(lat, lon)
