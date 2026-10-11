from fastapi import APIRouter, Query

from app import freshness
from app.services.medical import nearby

router = APIRouter()


@router.get("/medical")
async def medical(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                  kind: str = "dialysis", limit: int = Query(5, ge=1, le=25)):
    out = await nearby(lat, lon, kind, limit)
    if isinstance(out, dict):
        out["meta"] = freshness.snap_meta("dialysis", out.get("source") or "CMS Provider Data")
    return out
