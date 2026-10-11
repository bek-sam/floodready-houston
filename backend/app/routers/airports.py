from fastapi import APIRouter

from app.services.airports import get_status

router = APIRouter()


@router.get("/airports/status")
async def airports_status():
    return await get_status()
