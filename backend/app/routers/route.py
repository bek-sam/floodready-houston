from fastapi import APIRouter
from pydantic import BaseModel

from app import freshness
from app.services.route import check_route

router = APIRouter()


class Pt(BaseModel):
    lat: float
    lon: float


class RouteReq(BaseModel):
    origin: Pt
    destination: Pt


@router.post("/route-check")
async def route_check(body: RouteReq, simulate: str | None = None):
    out = await check_route(body.origin.model_dump(), body.destination.model_dump(), simulate=(simulate == "storm"))
    if isinstance(out, dict):
        out["meta"] = freshness.meta("OSRM routing + crossings snapshot + community reports", "live",
                                     storm=freshness.storm_on())
        out["meta"]["snapshot_date"] = freshness.snapshot_dates().get("crossings")
        if simulate == "storm":
            out["simulated"] = True
            out["meta"]["storm_mode"] = True
    return out


@router.get("/route-check/demo")
async def demo_routes():
    from app.services.route import DEMO_ROUTES
    return DEMO_ROUTES
