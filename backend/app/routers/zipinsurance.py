from fastapi import APIRouter, HTTPException

from app import freshness
from app.services.zipinsurance import valid_zip, zip_insurance

router = APIRouter()


@router.get("/zip-insurance")
async def get_zip_insurance(zip: str):
    if not valid_zip(zip):
        raise HTTPException(422, "zip must be 5 digits")
    out = await zip_insurance(zip)
    return freshness.with_meta(out, source=out.get("source", "OpenFEMA NFIP") if isinstance(out, dict) else "", freshness="recent", storm=False)
