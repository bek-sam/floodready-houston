from fastapi import APIRouter, HTTPException, Query

from app.services import gauge_history as svc

router = APIRouter()


@router.get("/gauges/{gauge_id}/history")
async def history(gauge_id: str, hours: int = Query(48, ge=1, le=168)):
    d = await svc.history(gauge_id, hours)
    if d is None:
        raise HTTPException(404, "Unknown gauge")
    return d
