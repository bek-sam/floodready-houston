from fastapi import APIRouter, HTTPException

from app import freshness
from app.services.floodhistory import flood_history
from app.services.zipinsurance import valid_zip

router = APIRouter()


@router.get("/flood-history")
async def get_flood_history(lat: float, lon: float, zip: str | None = None):
    if zip is not None and not valid_zip(zip):
        raise HTTPException(422, "zip must be 5 digits")
    out = await flood_history(lat, lon, zip)
    return freshness.with_meta(out, source="City of Houston Harvey extent + replay gauges + OpenFEMA", freshness="historical",
                               as_of="2017-08-31T00:00:00+00:00", storm=False)
