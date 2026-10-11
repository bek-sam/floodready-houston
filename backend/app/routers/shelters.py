from fastapi import APIRouter

from app import freshness
from app.services.shelters import get_shelters

router = APIRouter()


@router.get("/shelters")
async def shelters(lat: float, lon: float, pet_friendly: bool = False, limit: int = 10):
    out = await get_shelters(lat, lon, pet_friendly, min(max(limit, 1), 50))
    out["meta"] = freshness.meta(out.get("source", ""), "historical", as_of="2017-09-01T00:00:00+00:00", storm=False)
    return out
