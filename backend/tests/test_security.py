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
