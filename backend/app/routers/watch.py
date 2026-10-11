from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import freshness
from app.db import Place, get_session
from app.services.watch import evaluate

router = APIRouter()


class PlaceIn(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    lang: Optional[str] = Field(default="en", max_length=8)


def _row(p: Place) -> dict:
    return {"id": p.id, "label": p.label, "lat": p.lat, "lon": p.lon, "lang": p.lang}


@router.post("/watch")
async def add_place(body: PlaceIn):
    try:
        with get_session() as s:
            p = Place(**body.model_dump())
            s.add(p)
            s.commit()
            s.refresh(p)
            return _row(p)
    except Exception as e:
        raise HTTPException(503, f"Storage unavailable: {type(e).__name__}")


@router.get("/watch/status")
async def status(ids: str = "", simulate: str | None = None):
    wanted = [i for i in ids.split(",") if i][:20]
    try:
        with get_session() as s:
            places = [_row(p) for p in s.query(Place).filter(Place.id.in_(wanted)).all()] if wanted else []
    except Exception:
        places = []
    out = [await evaluate(p, simulate == "storm") for p in places]
    return {"places": out, "meta": freshness.meta("NWS alerts + NOAA NWPS gauges", "live",
                                                    storm=any((o.get("meta") or {}).get("storm_mode") for o in out))}
