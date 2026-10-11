from fastapi import APIRouter, Query

from app.services.geo import geocode as _geocode

router = APIRouter()


@router.get("/geocode")
async def geocode(q: str = Query(..., min_length=2)):
    return await _geocode(q)
