from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import freshness
from app.db import Report, ReportVote, get_session
from app.services.route import REPORT_MAX_AGE_H, is_cleared, vote_counts

router = APIRouter()
SOURCE = "FloodReady community reports (unverified)"


class ReportIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    kind: Literal["flooded_road", "water_over_road", "barricade_missing", "stalled_vehicles", "other"] = "flooded_road"
    depth_in: Optional[float] = Field(default=None, ge=0, le=500)
    note: Optional[str] = Field(default=None, max_length=1000)


class VoteIn(BaseModel):
    still_there: bool


def _row(r: Report, vc: dict | None = None) -> dict:
    vc = vc or {}
    return {"id": r.id, "lat": r.lat, "lon": r.lon, "kind": r.kind, "depth_in": r.depth_in,
            "note": r.note, "created_at": r.created_at.isoformat() if r.created_at else None,
            "confirms": vc.get("confirms", 0), "clears": vc.get("clears", 0),
            "last_vote_at": vc.get("last_vote_at"), "cleared": is_cleared(vc)}


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


@router.post("/reports/{report_id}/vote")
async def vote_report(report_id: str, body: VoteIn):
    try:
        with get_session() as s:
            if s.query(Report).filter(Report.id == report_id).first() is None:
                raise HTTPException(404, "Unknown report")
            s.add(ReportVote(report_id=report_id, still_there=body.still_there))
            s.commit()
            vc = vote_counts(s, [report_id]).get(report_id, {})
            return {"id": report_id, "confirms": vc.get("confirms", 0), "clears": vc.get("clears", 0),
                    "last_vote_at": vc.get("last_vote_at"), "cleared": is_cleared(vc)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"Report storage unavailable: {type(e).__name__}")


@router.get("/reports")
async def list_reports(limit: int = 200, since_hours: float = REPORT_MAX_AGE_H):
    """Recent reports (default last 6 h, same window the route check uses). since_hours up to 168 lists history."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max(0.0, min(since_hours, 168.0)))
    try:
        with get_session() as s:
            rows = s.query(Report).order_by(Report.created_at.desc()).limit(min(limit, 1000)).all()
            keep = []
            for r in rows:
                ts = r.created_at
                if ts is not None and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts is None or ts < cutoff:
                    continue
                if r.kind in ("flooded_road", "water_over_road", "barricade_missing", "stalled_vehicles", "other") \
                        and not (r.depth_in == 0 and not r.note):
                    keep.append(r)
            votes = vote_counts(s, [r.id for r in keep])
            return [_row(r, votes.get(r.id)) for r in keep]
    except Exception:
        return []
