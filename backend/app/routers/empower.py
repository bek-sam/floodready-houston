from fastapi import APIRouter, HTTPException

from app import freshness
from app.services.empower import SOURCE, get_empower, valid_zip

router = APIRouter()


@router.get("/empower")
async def empower(zip: str):
    if not valid_zip(zip):
        raise HTTPException(422, "zip must be 5 digits")
    out = await get_empower(zip)
    out["meta"] = freshness.meta(SOURCE, "live" if out["available"] else "cached")
    return out
