from fastapi import APIRouter

from app.services.reservoir import get_pool

router = APIRouter()


@router.get("/reservoir/pool")
async def reservoir_pool(lat: float, lon: float):
    return await get_pool(lat, lon)
