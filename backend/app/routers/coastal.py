from fastapi import APIRouter

from app import freshness
from app.services.coastal import coastal

router = APIRouter()


@router.get("/coastal")
async def get_coastal():
    out = await coastal()
    t = out["tide"]
    fr = "unavailable" if t["observed_ft"] is None else ("stale" if t.get("stale") else "live")
    as_of = t["as_of"].replace(" ", "T") + ":00+00:00" if t.get("as_of") else None
    return freshness.with_meta(out, source="NOAA CO-OPS station 8771450 + NHC CurrentStorms", freshness=fr, as_of=as_of)
