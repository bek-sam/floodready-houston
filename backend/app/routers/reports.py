from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import Report, get_session

router = APIRouter()


class ReportIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    kind: Literal["flooded_road", "water_over_road", "barricade_missing", "stalled_vehicles", "other"] = "flooded_road"
    depth_in: Optional[float] = Field(default=None, ge=0, le=500)
    note: Optional[str] = Field(default=None, max_length=1000)


def _row(r: Report) -> dict:
    return {"id": r.id, "lat": r.lat, "lon": r.lon, "kind": r.kind, "depth_in": r.depth_in,
            "note": r.note, "created_at": r.created_at.isoformat() if r.created_at else None}


@router.post("/reports")
async def create_report(body: ReportIn):
    try:
        with get_session() as s:
            r = Report(**body.model_dump())
            s.add(r)
            s.commit()
            s.refresh(r)
            return _row(r)
    except Exception as e:
        raise HTTPException(503, f"Report storage unavailable: {type(e).__name__}")


@router.get("/reports")
async def list_reports(limit: int = 200):
    try:
        with get_session() as s:
            rows = s.query(Report).order_by(Report.created_at.desc()).limit(min(limit, 1000)).all()
            return [_row(r) for r in rows]
    except Exception:
        return []
