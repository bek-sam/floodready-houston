from datetime import datetime, timezone

from fastapi import APIRouter

from app import freshness
from app.services.evac import evac_at

router = APIRouter()


@router.get("/evac")
async def get_evac(lat: float, lon: float):
    out = await evac_at(lat, lon)
    stale, ts = out.pop("_stale"), out.pop("_as_of")
    as_of = datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None
    return freshness.with_meta(out, source="Harris County GIS evacuation zones + NOAA NHC storm-surge risk maps",
                               freshness="stale" if stale else "live", as_of=as_of, storm=False)
