from fastapi import APIRouter

from app.services.alerts import area_alerts, get_alerts

router = APIRouter()


@router.get("/alerts")
async def alerts(lat: float, lon: float):
    return await get_alerts(lat, lon)


@router.get("/alerts/area")
async def alerts_area(bbox: str = "-96.5,29,-94.5,30.5"):
    return await area_alerts(bbox)
