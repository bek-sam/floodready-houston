from fastapi import APIRouter

from app.services.risk import get_risk

router = APIRouter()


@router.get("/risk")
async def risk(lat: float, lon: float, simulate: str | None = None):
    out = await get_risk(lat, lon, simulate=(simulate == "storm"))
    if simulate == "storm" and isinstance(out, dict):
        out["simulated"] = True
        out["meta"] = {**(out.get("meta") or {}), "storm_mode": True}
    return out
