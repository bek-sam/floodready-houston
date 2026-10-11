from fastapi import APIRouter

from app.services.alerts import add_simulated_alert, area_alerts, get_alerts

router = APIRouter()


@router.get("/alerts")
async def alerts(lat: float, lon: float, simulate: str | None = None):
    out = await get_alerts(lat, lon)
    if simulate == "storm":
        out = add_simulated_alert(out, lat, lon)
    return out


@router.get("/alerts/area")
async def alerts_area(bbox: str = "-96.5,29,-94.5,30.5"):
    return await area_alerts(bbox)
