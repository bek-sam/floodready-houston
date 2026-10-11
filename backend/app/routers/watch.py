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


# Houston region bbox (same as the area-alerts default): lon -96.5..-94.5, lat 29.0..30.5
REGION = (-96.5, 29.0, -94.5, 30.5)


def in_region(lat: float, lon: float) -> bool:
    return REGION[0] <= lon <= REGION[2] and REGION[1] <= lat <= REGION[3]


def _row(p: Place) -> dict:
    return {"id": p.id, "label": p.label, "lat": p.lat, "lon": p.lon, "lang": p.lang}


@router.post("/watch")
async def add_place(body: PlaceIn):
    if not in_region(body.lat, body.lon):
        raise HTTPException(422, {"code": "watch.outOfRegion",
                                  "message": "FloodReady watches places in the Houston area only (lat 29.0-30.5, lon -96.5 to -94.5)."})
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
    sim = simulate == "storm"
    res = {"places": out, "meta": freshness.meta("NWS alerts + NOAA NWPS gauges", "live",
                                                   storm=sim or any((o.get("meta") or {}).get("storm_mode") for o in out))}
    if sim:
        res["simulated"] = True
        for o in out:
            o["simulated"] = True
            o["meta"] = {**(o.get("meta") or {}), "storm_mode": True}
    return res
