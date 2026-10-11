from fastapi import APIRouter, Query

from app import freshness
from app.services.declarations import SOURCE, status

router = APIRouter()


@router.get("/declarations")
async def get_declarations(county: str = Query("Harris", min_length=1, max_length=60),
                           state: str = Query("TX", min_length=2, max_length=2)):
    out = await status(county, state)
    return freshness.with_meta(out, source=SOURCE, freshness="live" if out["available"] else "cached")
