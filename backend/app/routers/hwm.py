from fastapi import APIRouter, Query

from app import freshness
from app.services.hwm import nearby

router = APIRouter()


@router.get("/hwm")
async def get_hwm(lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
                  radius_mi: float = Query(2.0, gt=0, le=25)):
    out = nearby(lat, lon, radius_mi)
    snap = out.pop("snapshot_date", None)
    return freshness.with_meta(out, source=out["source"], freshness="historical",
                               as_of="2017-09-18T00:00:00+00:00", snapshot_date=snap, storm=False)
