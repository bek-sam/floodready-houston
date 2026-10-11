"""GET /harvey/extent?bbox=minx,miny,maxx,maxy&limit= -> simplified Harvey inundation GeoJSON."""
from fastapi import APIRouter, HTTPException, Query

from app import freshness
from app.services.harvey import extent_geojson

router = APIRouter(prefix="/harvey", tags=["harvey"])


@router.get("/extent")
async def extent(bbox: str = Query(..., description="minx,miny,maxx,maxy (lon/lat)"),
                 limit: int = Query(1500, ge=1, le=5000)):
    try:
        b = [float(v) for v in bbox.split(",")]
        assert len(b) == 4 and b[0] < b[2] and b[1] < b[3]
        assert -180 <= b[0] and b[2] <= 180 and -90 <= b[1] and b[3] <= 90
    except Exception:
        raise HTTPException(422, "bbox must be minx,miny,maxx,maxy in lon/lat")
    out = extent_geojson(b, limit)
    if isinstance(out, dict):
        out["meta"] = freshness.meta("City of Houston Harvey inundation (TDO StormDrainage_Study)", "historical",
                                     as_of="2017-08-31T00:00:00+00:00", snapshot_date=freshness.snapshot_dates().get("harvey"),
                                     storm=False)
    return out
