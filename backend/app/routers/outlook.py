from fastapi import APIRouter

from app import freshness
from app.services.outlook import get_outlook

router = APIRouter()


@router.get("/outlook")
async def outlook(lat: float, lon: float, simulate: str | bool = False):
    sim = simulate is True or str(simulate).lower() in ("1", "true", "storm", "yes")
    out = await get_outlook(lat, lon, sim)
    return freshness.with_meta(out, source=out.get("source", "NOAA WPC") if isinstance(out, dict) else "", freshness="recent")
