import os
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.services import sms as svc

router = APIRouter()
XML = "application/xml"


class SimIn(BaseModel):
    # `from` is a Python keyword, so accept it via alias; `phone` also works.
    from_: str = Field(default="+15555550100", alias="from", max_length=32)
    body: str = Field(default="", max_length=1000)
    simulate: bool = False
    model_config = {"populate_by_name": True}


class CallIn(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    name: str = Field(default="", max_length=80)
    lang: str = Field(default="en", max_length=8)


async def _form(request: Request) -> dict:
    return dict(parse_qsl((await request.body()).decode("utf-8", "replace"), keep_blank_values=True))


def _check(request: Request, params: dict) -> None:
    url = os.getenv("TWILIO_WEBHOOK_URL") or str(request.url)
    if not svc.valid_signature(url, params, request.headers.get("x-twilio-signature")):
        raise HTTPException(403, "Invalid Twilio signature")


@router.post("/sms/inbound")
async def inbound(request: Request):
    params = await _form(request)
    _check(request, params)
    reply = await svc.handle(params.get("From", ""), params.get("Body", ""))
    return Response(svc.twiml(reply), media_type=XML)


@router.post("/sms/simulate")
async def simulate(body: SimIn):
    reply = await svc.handle(body.from_, body.body, simulate=body.simulate)
    return {"reply": reply, "simulated": bool(body.simulate and reply.startswith(svc.SIM_PREFIX))}


@router.get("/checkin/script")
async def script(lang: str = Query("en", max_length=8)):
    return svc.checkin_script(lang)


@router.post("/checkin/digit")
async def digit(request: Request, lang: str = "en"):
    params = await _form(request)
    _check(request, params)
    return Response(svc.digit_twiml(lang if lang in svc.SCRIPT else "en", params.get("Digits", "")), media_type=XML)


@router.post("/checkin/call")
async def call(body: CallIn):
    if not svc.twilio_configured():
        raise HTTPException(503, "Voice check-in is not configured (set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM)")
    # Configured: place the call through Twilio's REST API (stdlib only; no extra dependency).
    import base64, urllib.parse, urllib.request
    sid, tok, frm = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"], os.environ["TWILIO_FROM"]
    lang = body.lang if body.lang in svc.SCRIPT else "en"
    data = urllib.parse.urlencode({"To": body.phone, "From": frm, "Twiml": svc.checkin_twiml(lang)}).encode()
    req = urllib.request.Request(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json", data=data)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{sid}:{tok}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return {"ok": True, "status": r.status}
    except Exception as e:
        raise HTTPException(502, f"Twilio call failed: {type(e).__name__}")
