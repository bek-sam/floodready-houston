from fastapi import APIRouter

from app.services.alerts import get_alerts

router = APIRouter()


@router.get("/alerts")
async def alerts(lat: float, lon: float):
    return await get_alerts(lat, lon)
