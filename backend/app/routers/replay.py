from fastapi import APIRouter, HTTPException

from app import freshness
from app.services import replay as svc

router = APIRouter()


@router.get("/replay/events")
async def events():
    return svc.list_events()


@router.get("/replay/{event_id}")
async def event(event_id: str):
    d = svc.get_event(event_id)
    if d is None:
        raise HTTPException(404, "Unknown replay event")
    if isinstance(d, dict):
        ev = d.get("event") or {}
        d["meta"] = freshness.meta(ev.get("source") or "USGS / NOAA historical gauge data", "historical",
                                   as_of=(ev.get("end") or ev.get("start")), storm=False)
    return d
