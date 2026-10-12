"""Security hardening: push SSRF, SMS/call abuse, input caps, rate limits, vote dedupe, profile tokens,
demo snapshot gating, AI injection surfaces and service-level validation. Network is always mocked."""
import asyncio
import json

from tests.test_api import client  # noqa: F401  (reuses the mocked-network fixture)


# ---------- 1. push SSRF + blocking send ----------

def test_push_endpoint_allowlist():
    from app.services.push import endpoint_allowed
    for ok in ("https://fcm.googleapis.com/fcm/send/abc", "https://updates.push.services.mozilla.com/wpush/v2/x",
               "https://web.push.apple.com/QGx", "https://wns2-par02p.notify.windows.com/w/?token=1",
               "https://android.googleapis.com/gcm/send/x"):
        assert endpoint_allowed(ok), ok
    for bad in ("http://fcm.googleapis.com/fcm/send/abc", "https://169.254.169.254/latest/meta-data",
                "https://localhost/x", "https://evil.com/fcm.googleapis.com", "https://fcm.googleapis.com.evil.com/x",
                "https://notfcm.googleapis.com.attacker.io/", "https://fcm.googleapis.com:8443/x",
                "https://user:pw@fcm.googleapis.com/x", "file:///etc/passwd", "", None):
        assert not endpoint_allowed(bad), bad


def test_push_subscribe_rejects_internal_endpoint(client):
    sub = {"endpoint": "http://127.0.0.1:8000/admin", "keys": {"p256dh": "a", "auth": "b"}}
    r = client.post("/api/push/subscribe", json={"subscription": sub})
    assert r.status_code == 422


def test_push_send_uses_timeout_and_thread(client, monkeypatch, tmp_path):
    import threading
    from app.services import push as P
    monkeypatch.setattr(P, "VAPID_FILE", tmp_path / "v.json")
    P._vapid_cache.clear()
    seen = {}

    def fake_webpush(info, data, **kw):
        seen["timeout"] = kw.get("timeout")
        seen["thread"] = threading.current_thread() is threading.main_thread()
    monkeypatch.setattr(P, "webpush", fake_webpush)
    sub = {"endpoint": "https://fcm.googleapis.com/fcm/send/t1", "keys": {"p256dh": "a", "auth": "b"}}
    assert client.post("/api/push/subscribe", json={"subscription": sub}).status_code == 200
    assert client.post("/api/push/test", json={"endpoint": sub["endpoint"]}).json() == {"sent": 1}
    assert seen == {"timeout": 10, "thread": False}


def test_push_send_skips_disallowed_stored_endpoint(monkeypatch, tmp_path):
    from app.services import push as P
    from app.db import PushSub
    called = []
    monkeypatch.setattr(P, "webpush", lambda *a, **k: called.append(1))
    assert P.send_one(PushSub(endpoint="http://10.0.0.1/x", keys="{}"), {}) == "gone" and not called


# ---------- 2. SMS simulator + phone calls ----------

def _optin(phone):
    from app.db import get_session
    from app.services.sms import SmsOptIn
    with get_session() as s:
        return s.get(SmsOptIn, phone)


def test_sms_simulate_does_not_persist_by_default(client, monkeypatch):
    monkeypatch.delenv("SMS_SIMULATE", raising=False)
    monkeypatch.delenv("DEMO_SNAPSHOT", raising=False)
    r = client.post("/api/sms/simulate", json={"from": "+17135550101", "body": "ALERTS ON 77096"}).json()
    assert "saved" in r["reply"]  # same reply as before
    assert _optin("+17135550101") is None
    client.post("/api/sms/simulate", json={"from": "+17135550101", "body": "STOP"})
    assert _optin("+17135550101") is None


def test_sms_simulate_persists_when_enabled(client, monkeypatch):
    monkeypatch.setenv("SMS_SIMULATE", "1")
    client.post("/api/sms/simulate", json={"from": "+17135550102", "body": "ALERTS ON 77096"})
    assert _optin("+17135550102").opted_in is True


def test_checkin_call_needs_flag_and_runs_off_loop(client, monkeypatch):
    import threading
    import urllib.request
    for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"):
        monkeypatch.setenv(k, "x")
    monkeypatch.delenv("CHECKIN_CALLS", raising=False)
    body = {"phone": "+17135550103", "name": "A", "lang": "en"}
    calls = []

    class Resp:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        calls.append(threading.current_thread() is threading.main_thread())
        return Resp()
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert client.post("/api/checkin/call", json=body).status_code == 503 and not calls
    monkeypatch.setenv("CHECKIN_CALLS", "1")
    assert client.post("/api/checkin/call", json=body).json() == {"ok": True, "status": 201}
    assert calls == [False]


def test_checkin_call_rate_limited(client, monkeypatch):
    from app import ratelimit
    ratelimit.reset()
    monkeypatch.delenv("CHECKIN_CALLS", raising=False)
    codes = [client.post("/api/checkin/call", json={"phone": "+17135550104"}).status_code for _ in range(5)]
    assert codes[0] == 503 and codes[-1] == 429
    ratelimit.reset()


# ---------- 3. question / history caps ----------

def test_ask_caps_question_lang_history(client):
    from app import ratelimit
    ratelimit.reset()
    long_q = {"question": "x" * 501, "lang": "en"}
    assert client.post("/api/ask", json=long_q).status_code == 422
    assert client.post("/api/ask/stream", json=long_q).status_code == 422  # middleware guard covers the stream too
    many = [{"role": "user", "content": "hi"}] * 13
    assert client.post("/api/ask", json={"question": "hi", "history": many}).status_code == 422
    huge = [{"role": "user", "content": "x" * 2001}]
    assert client.post("/api/ask", json={"question": "hi", "history": huge}).status_code == 422
    assert client.post("/api/ask", json={"question": "hi", "lang": "x" * 17}).status_code == 422


def test_ask_unknown_lang_falls_back_to_en():
    from app.ai.router import AskBody
    assert AskBody(question="hi", lang="klingon").lang == "en"
    assert AskBody(question="hi", lang="es").lang == "es"


# ---------- 4. rate limits on paid endpoints + live WebSocket ----------

def test_paid_endpoints_rate_limited(client, monkeypatch):
    from app import ratelimit
    ratelimit.reset()
    monkeypatch.setattr(ratelimit, "LIMITS", [(p, 2, w) for p, _, w in ratelimit.LIMITS])
    for method, path in (("GET", "/api/geocode?q=77096"), ("GET", "/api/el-agent/signed-url"),
                         ("POST", "/api/voice"), ("GET", "/api/voice/filler?lang=en"), ("GET", "/api/profile/abc"),
                         ("POST", "/api/route-check"), ("POST", "/api/sms/simulate"), ("POST", "/api/profile")):
        codes = [client.request(method, path, json={}).status_code for _ in range(3)]
        assert codes[-1] == 429, (path, codes)
    assert client.get("/api/reports").status_code == 200  # plain reads stay unlimited
    ratelimit.reset()


def test_ratelimit_evicts_stale_ips(monkeypatch):
    from app import ratelimit
    ratelimit.reset()
    t = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: t[0])
    ratelimit._last_sweep = t[0]
    for i in range(50):
        ratelimit._allowed(f"10.0.0.{i}", "/api/ask", 60, 60)
    assert len(ratelimit._hits) == 50
    t[0] += ratelimit.MAX_WINDOW + ratelimit.SWEEP_EVERY_S + 1
    ratelimit._allowed("10.0.1.1", "/api/ask", 60, 60)
    assert list(ratelimit._hits) == [("10.0.1.1", "/api/ask")]
    ratelimit.reset()


def _live_app():
    from fastapi import FastAPI
    from app.ai import live_router
    a = FastAPI()
    a.include_router(live_router.router)
    return a


def test_live_rejects_foreign_origin(monkeypatch):
    import pytest
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    from app.ai import live
    monkeypatch.setattr(live, "make_client", lambda: None)
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    c = TestClient(_live_app())
    with pytest.raises(WebSocketDisconnect):
        with c.websocket_connect("/live", headers={"origin": "https://evil.example"}) as ws:
            ws.receive_json()
    for origin in ("http://localhost:5173", "http://testserver"):  # CORS origin, same-origin
        with c.websocket_connect("/live", headers={"origin": origin}) as ws:
            assert ws.receive_json()["detail"].startswith("Gemini Live is not configured")


def test_live_per_ip_cap(monkeypatch):
    from fastapi.testclient import TestClient
    from app.ai import live, live_router
    monkeypatch.setattr(live, "make_client", lambda: object())
    monkeypatch.setattr(live_router, "_per_ip", {"testclient": live_router.MAX_PER_IP})
    with TestClient(_live_app()).websocket_connect("/live") as ws:
        assert "this device" in ws.receive_json()["detail"]
    assert live_router._active == 0
