"""Web Push: VAPID keys, sending, and the background watch loop."""
import asyncio
import base64
import json
import logging
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from app.db import Place, PushSub, get_session
from app.services.watch import RANK, evaluate

log = logging.getLogger("push")
VAPID_FILE = Path(__file__).resolve().parents[2] / ".vapid.json"
INTERVAL_S = 300
CALL = {"en": "Call 911 in an emergency.", "es": "Llame al 911 en una emergencia.",
        "vi": "Gọi 911 khi có trường hợp khẩn cấp.", "zh": "紧急情况请拨打 911。", "ar": "اتصل بالرقم 911 في حالات الطوارئ."}
TEXT = {
    "en": {"warning": ("Flood warning", "Flood warning for {label}: avoid low roads and underpasses."),
           "watch": ("Flood watch", "Flood watch for {label}: conditions are building. Check routes before driving."),
           "test": ("FloodReady test", "Notifications are working.")},
    "es": {"warning": ("Alerta de inundacion", "Alerta de inundacion para {label}: evite calles bajas y pasos a desnivel."),
           "watch": ("Vigilancia de inundacion", "Vigilancia de inundacion para {label}: las condiciones empeoran. Revise su ruta antes de manejar."),
           "test": ("Prueba de FloodReady", "Las notificaciones funcionan.")},
    "vi": {"warning": ("Cảnh báo lũ", "Cảnh báo lũ cho {label}: tránh đường thấp và hầm chui."),
           "watch": ("Theo dõi lũ", "Theo dõi lũ cho {label}: tình hình đang xấu đi. Kiểm tra tuyến đường trước khi lái xe."),
           "test": ("Thử nghiệm FloodReady", "Thông báo đang hoạt động.")},
    "zh": {"warning": ("洪水警告", "{label} 洪水警告：请避开低洼道路和下穿通道。"),
           "watch": ("洪水监视", "{label} 洪水监视：情况正在恶化。出行前请先查看路线。"),
           "test": ("FloodReady 测试", "通知功能正常。")},
    "ar": {"warning": ("تحذير من الفيضان", "تحذير من الفيضان في {label}: تجنب الطرق المنخفضة والأنفاق."),
           "watch": ("مراقبة الفيضان", "مراقبة الفيضان في {label}: الأوضاع تتفاقم. تحقق من مسارك قبل القيادة."),
           "test": ("اختبار FloodReady", "الإشعارات تعمل.")},
}


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _pub_b64(v: Vapid) -> str:
    return _b64(v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))


_vapid_cache: dict = {}


def get_vapid() -> tuple[Vapid, str, str]:
    """(vapid, public_key_b64, subject). Env keys if set, else generated once into backend/.vapid.json."""
    if _vapid_cache:
        return _vapid_cache["v"]
    subject = os.getenv("VAPID_SUBJECT") or "mailto:floodready@example.com"
    priv, pub = os.getenv("VAPID_PRIVATE_KEY"), os.getenv("VAPID_PUBLIC_KEY")
    if priv:
        v = Vapid.from_string(priv)
        res = (v, pub or _pub_b64(v), subject)
    else:
        v = None
        try:
            v = Vapid.from_pem(json.loads(VAPID_FILE.read_text())["private_pem"].encode())
        except Exception:
            v = Vapid()
            v.generate_keys()
            pem = v.private_pem().decode()
            try:
                VAPID_FILE.write_text(json.dumps({"private_pem": pem, "public_key": _pub_b64(v)}))
                VAPID_FILE.chmod(0o600)
            except Exception as e:
                log.warning("could not persist VAPID keys: %s", e)
        res = (v, _pub_b64(v), subject)
    _vapid_cache["v"] = res
    return res


def vapid_public_key() -> str:
    return get_vapid()[1]


def _sub_info(sub: PushSub) -> dict:
    return {"endpoint": sub.endpoint, "keys": json.loads(sub.keys)}


def send_one(sub: PushSub, payload: dict) -> str:
    """'ok' | 'gone' (404/410, delete it) | 'error'."""
    v, _, subject = get_vapid()
    try:
        webpush(_sub_info(sub), json.dumps(payload), vapid_private_key=v, vapid_claims={"sub": subject})
        return "ok"
    except WebPushException as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        log.warning("push failed (%s): %s", code, e)
        return "gone" if code in (404, 410) else "error"
    except Exception as e:
        log.warning("push error: %s", e)
        return "error"


def make_payload(lang: str, level: str, label: str, place_id: str = "test") -> dict:
    t = TEXT.get(lang, TEXT["en"])
    title, body = t[level] if level in t else t["test"]
    return {"title": title, "body": f"{body.format(label=label)} {CALL.get(lang, CALL['en'])}".strip(),
            "url": "/#watch", "tag": f"floodready-{place_id}", "level": level}


def _places_for(s, sub: PushSub) -> list[dict]:
    ids = json.loads(sub.place_ids or "[]")
    if not ids:
        return []
    return [{"id": p.id, "label": p.label, "lat": p.lat, "lon": p.lon, "lang": p.lang}
            for p in s.query(Place).filter(Place.id.in_(ids)).all()]


def _process_status(s, sub: PushSub, payload: dict) -> str:
    """Send; delete the subscription if gone (404/410). Returns 'ok' | 'gone' | 'error'."""
    r = send_one(sub, payload)
    if r == "gone":
        s.delete(sub)
        s.commit()
    return r


def _process(s, sub: PushSub, payload: dict) -> bool:
    return _process_status(s, sub, payload) == "ok"


async def push_test(endpoint: str) -> int:
    sent = 0
    with get_session() as s:
        for sub in s.query(PushSub).filter(PushSub.endpoint == endpoint).all():
            if _process(s, sub, make_payload(sub.lang or "en", "test", "")):
                sent += 1
    return sent


async def push_simulate(endpoint: str) -> int:
    sent = 0
    with get_session() as s:
        for sub in s.query(PushSub).filter(PushSub.endpoint == endpoint).all():
            for p in _places_for(s, sub):
                ev = await evaluate(p, True)
                if _process(s, sub, make_payload(sub.lang or "en", ev["level"], p["label"], p["id"])):
                    sent += 1
    return sent


async def check_all() -> int:
    """One pass of the background loop: push only when a place's level rises."""
    sent = 0
    with get_session() as s:
        for sub in list(s.query(PushSub).all()):
            last = json.loads(sub.last_levels or "{}")
            new = dict(last)
            gone = False
            for p in _places_for(s, sub):
                ev = await evaluate(p, False)
                prev = last.get(p["id"], "ok")
                if RANK[ev["level"]] > RANK[prev]:
                    r = _process_status(s, sub, make_payload(sub.lang or "en", ev["level"], p["label"], p["id"]))
                    if r == "ok":
                        sent += 1
                        new[p["id"]] = ev["level"]
                    elif r == "gone":
                        gone = True
                        break
                    # failed send: keep the previous level so the next pass retries
                else:
                    new[p["id"]] = ev["level"]  # level fell or unchanged: track it so a later rise alerts again
            if gone:
                continue
            try:
                sub.last_levels = json.dumps(new)
                s.commit()
            except Exception:
                s.rollback()
    try:
        from app.services.sms import send_level_rises
        sent += await send_level_rises()
    except Exception as e:
        log.warning("sms alert pass failed: %s", e)
    return sent


async def loop():
    await asyncio.sleep(30)
    while True:
        try:
            await check_all()
        except Exception as e:
            log.warning("push loop error: %s", e)
        await asyncio.sleep(INTERVAL_S)
