from fastapi import APIRouter, HTTPException

from app.services.geo import geocode
from app.services.parking import assess

router = APIRouter()


@router.get("/parking/check")
async def parking_check(lat: float | None = None, lon: float | None = None, q: str | None = None, simulate: str | None = None):
    address = None
    if lat is None or lon is None:
        if not q or len(q) < 2:
            raise HTTPException(422, "Provide lat and lon, or q (address)")
        g = await geocode(q)
        if g.get("lat") is None:
            raise HTTPException(404, "Address not found")
        lat, lon, address = g["lat"], g["lon"], g.get("matched_address")
    return await assess(lat, lon, address, simulate=(simulate == "storm"))
