from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json

from app.db import PushSub, get_session
from app.services import push as svc

router = APIRouter()


class SubIn(BaseModel):
    subscription: dict[str, Any]
    place_ids: list[str] = Field(default_factory=list, max_length=50)
    lang: str = Field(default="en", max_length=8)


class EndpointIn(BaseModel):
    endpoint: str | None = None


@router.get("/push/vapid-public-key")
async def vapid_key():
    return {"key": svc.vapid_public_key()}


@router.post("/push/subscribe")
async def subscribe(body: SubIn):
    ep, keys = body.subscription.get("endpoint"), body.subscription.get("keys")
    if not ep or not isinstance(keys, dict) or not keys.get("p256dh") or not keys.get("auth"):
        raise HTTPException(422, "Invalid push subscription")
    try:
        with get_session() as s:
            sub = s.query(PushSub).filter(PushSub.endpoint == ep).first() or PushSub(endpoint=ep)
            sub.keys = json.dumps({"p256dh": keys["p256dh"], "auth": keys["auth"]})
            sub.place_ids = json.dumps(body.place_ids)
            sub.lang = body.lang if body.lang in svc.TEXT else "en"
            sub.last_levels = "{}"
            s.add(sub)
            s.commit()
            return {"id": sub.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"Storage unavailable: {type(e).__name__}")


@router.post("/push/unsubscribe")
async def unsubscribe(body: EndpointIn):
    if not body.endpoint:
        raise HTTPException(422, "endpoint is required")
    with get_session() as s:
        n = s.query(PushSub).filter(PushSub.endpoint == body.endpoint).delete()
        s.commit()
    return {"ok": n > 0}


def _require_known(endpoint: str | None) -> str:
    if not endpoint:
        raise HTTPException(400, "endpoint is required")
    with get_session() as s:
        if not s.query(PushSub).filter(PushSub.endpoint == endpoint).first():
            raise HTTPException(404, "Unknown subscription")
    return endpoint


@router.post("/push/test")
async def test(body: EndpointIn):
    return {"sent": await svc.push_test(_require_known(body.endpoint))}


@router.post("/push/simulate")
async def simulate(body: EndpointIn):
    return {"sent": await svc.push_simulate(_require_known(body.endpoint))}
