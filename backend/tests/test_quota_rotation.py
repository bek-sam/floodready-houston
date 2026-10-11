import asyncio

import pytest

from app.ai import config, fast


class E429(Exception):
    pass


@pytest.fixture(autouse=True)
def _iso(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "QUOTA_FILE", tmp_path / "quota.json")
    monkeypatch.setattr(config, "_state", {})
    monkeypatch.setenv("GEMINI_API_KEY", "k1")
    monkeypatch.setenv("GEMINI_API_KEYS", "k2,k1")
    for v in ("GEMINI_CHAT_MODEL", "GEMINI_VOICE_MODEL"):
        monkeypatch.delenv(v, raising=False)


def test_keys_dedup():
    assert config.gemini_keys() == ["k2", "k1"]


def test_retry_delay_parse():
    assert config.retry_delay_s(Exception("429 RESOURCE_EXHAUSTED 'retryDelay': '34s'")) == 34
    assert config.retry_delay_s(Exception("429")) == 3600


def test_rotation_persists_and_skips(monkeypatch):
    config.mark_exhausted("k1", "gemini-3.1-flash-lite", Exception("429 retry in 50s"))
    assert config.is_exhausted("k1", "gemini-3.1-flash-lite")
    assert ("k1", "gemini-3.1-flash-lite") not in config.pairs(config.chat_models())
    assert config._load() and config.QUOTA_FILE.exists()


def test_gemini_once_rotates(monkeypatch):
    calls = []

    class R:
        text = "ok"
        usage_metadata = None

    class Models:
        async def generate_content(self, model, contents, config):
            calls.append(model)
            if model != "gemini-3.5-flash-lite":
                raise E429("429 RESOURCE_EXHAUSTED")
            return R()

    class Cl:
        class aio:
            models = Models()

    monkeypatch.setattr(fast, "_client", lambda t, g, key=None: Cl())
    monkeypatch.setattr(fast, "_ctx_cache", lambda *a, **k: None)
    monkeypatch.setattr(fast, "_configs", lambda *a, **k: [None])
    out = asyncio.run(fast.gemini_once("s", "p"))
    assert out == "ok" and config.last_model.get() == "gemini-3.5-flash-lite"
    assert config.is_exhausted("k2", "gemini-3.1-flash-lite")
    assert calls[-1] == "gemini-3.5-flash-lite"


def test_quota_status_no_keys():
    config.mark_exhausted("k1", "gemini-3.1-flash-lite")
    config.mark_exhausted("k2", "gemini-3.1-flash-lite")
    st = config.quota_status()
    assert st["models_exhausted"] == 1 and "k1" not in str(st)
