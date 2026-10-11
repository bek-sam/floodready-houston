import time

from fastapi.testclient import TestClient


def test_startup_shutdown_fast():
    from app.main import app
    t = time.monotonic()
    with TestClient(app) as c:
        assert c.get("/api/health").status_code == 200
    assert time.monotonic() - t < 3


def test_el_agent_503_without_id(monkeypatch):
    from app.main import app
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    with TestClient(app) as c:
        r = c.get("/api/el-agent/signed-url")
    assert r.status_code == 503 and "detail" in r.json()
