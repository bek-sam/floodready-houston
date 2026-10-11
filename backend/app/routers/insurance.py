from fastapi import APIRouter

from app.services.insurance import insurance_countdown

router = APIRouter()


@router.get("/insurance/countdown")
async def countdown(purchase_date: str | None = None):
    return await insurance_countdown(purchase_date)
