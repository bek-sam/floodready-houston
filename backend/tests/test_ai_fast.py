"""Fast voice path: SSE ask, streaming TTS, filler. Mocks only."""
import json
import types as pytypes

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import fast, graph, rag, voice
from app.ai.router import router

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)
GOOD = "https://example.org/good"


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(voice, "CACHE", tmp_path / "voice")
    monkeypatch.setattr(rag, "search", lambda q, k=4: [
        {"kind": "fact", "file": "x.md", "title": "T", "text": "Flood insurance takes 30 days.", "source": GOOD, "score": 1}])

    async def fake_tool(name, args):
        return {"ok": name, "source": GOOD}
    monkeypatch.setattr(fast, "run_tool", fake_tool)


def events(resp):
    return [json.loads(b[6:]) for b in resp.text.split("\n\n") if b.startswith("data: ")]


def test_split_sentences():
    s, rest = fast.split_sentences("One. Two! Thr")
    assert s == ["One.", "Two!"] and rest == "Thr"
    assert fast.split_sentences("Thr", True) == (["Thr"], "")


def test_template_fallback_stream():
    r = client.post("/api/ask/stream", json={"question": "Did my neighborhood flood before?", "lat": 29.7, "lon": -95.4})
    ev = events(r)
    assert r.headers["content-type"].startswith("text/event-stream")
    assert ev[0]["type"] == "speak" and ev[-1]["type"] == "final"
    assert ev[-1]["generated_by"] == "template" and "first_speak_ms" in ev[-1]["timings"]


def test_gemini_stream_sentences_and_citation_filter(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def fake(system, prompt, *a, **kw):
        assert "Live data" in prompt and "get_risk" in prompt
        for c in ["Yes, it flooded in **Harvey**. See ", GOOD + " and https://evil.example/x. Be", "ware of water. Not official guidance."]:
            yield c
    monkeypatch.setattr(fast, "gemini_stream", fake)
    ev = events(client.post("/api/ask/stream", json={"question": "Did my neighborhood flood before?", "lat": 29.7, "lon": -95.4}))
    speaks = [e["text"] for e in ev if e["type"] == "speak"]
    assert speaks[0] == "Yes, it flooded in Harvey."
    assert all("http" not in t and "*" not in t for t in speaks)
    fin = ev[-1]
    assert fin["generated_by"] == "gemini" and fin["sources"] == [GOOD]
    assert "evil.example" not in fin["answer"]
    assert set(fin["tools_used"]) == {"get_risk", "get_flood_history"}


def test_gemini_error_falls_back_to_template(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def boom(system, prompt, *a, **kw):
        raise RuntimeError("x")
        yield
    monkeypatch.setattr(fast, "gemini_stream", boom)
    ev = events(client.post("/api/ask/stream", json={"question": "insurance waiting period?"}))
    assert ev[-1]["type"] == "final" and ev[-1]["generated_by"] == "template"


def test_voice_stream_and_filler(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    calls = []

    class TTS:
        def stream(self, **kw):
            calls.append(kw)
            yield b"aa"
            yield b"bb"

    class FakeEL:
        def __init__(self, api_key):
            self.text_to_speech = TTS()
    import elevenlabs.client as ec
    monkeypatch.setattr(ec, "ElevenLabs", FakeEL)
    r = client.post("/api/voice/stream", json={"text": "hello", "lang": "en"})
    assert r.content == b"aabb" and r.headers["content-type"] == "audio/mpeg"
    assert calls[0]["model_id"] == "eleven_flash_v2_5"
    r2 = client.post("/api/voice/stream", json={"text": "hello", "lang": "en"})  # cached
    assert r2.content == b"aabb" and len(calls) == 1
    monkeypatch.setattr(voice, "synthesize", lambda t, l: b"filler:" + t.encode())
    f = client.get("/api/voice/filler?lang=es")
    assert f.status_code == 200 and f.content.startswith(b"filler:Un momento")


def test_voice_stream_no_key(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    assert client.post("/api/voice/stream", json={"text": "x"}).status_code == 503
    assert client.get("/api/voice/filler").status_code == 503


def test_street_flood_canned_es():
    ev = events(client.post("/api/ask/stream", json={"question": "¿Qué hago si mi calle se inunda?", "lang": "es", "lat": 29.7, "lon": -95.4}))
    speaks = [e["text"] for e in ev if e["type"] == "speak"]
    assert speaks == graph.STREET["es"]
    assert "911" in speaks[0] and ev[-1]["sources"] and ev[-1]["sources"][0].startswith("http")


def test_gemini_sources_and_localized_disclaimer(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def fake(system, prompt, *a, **kw):
        assert "accents" in system and "Not official guidance" not in system
        yield "Sí, su ubicación se inundó. Not official guidance."
    monkeypatch.setattr(fast, "gemini_stream", fake)
    ev = events(client.post("/api/ask/stream", json={"question": "¿Se inundó antes mi barrio?", "lang": "es", "lat": 29.7, "lon": -95.4}))
    fin = ev[-1]
    assert GOOD in fin["sources"]
    assert fin["answer"].endswith(graph.DISCLAIMER["es"]) and "Not official" not in fin["answer"]
    assert [e["text"] for e in ev if e["type"] == "speak"] == ["Sí, su ubicación se inundó."]


def test_ask_street_flood_is_canned_even_with_key(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def boom(*a, **k):
        raise AssertionError("gemini must not be called")
    monkeypatch.setattr(fast, "gemini_once", boom)
    monkeypatch.setattr(graph, "ask", boom)
    j = client.post("/api/ask", json={"question": "My street is flooding, what do I do?", "lang": "es", "lat": 29.7, "lon": -95.4}).json()
    assert j["generated_by"] == "template" and "911" in j["answer"] and "warnings" not in j


def test_ask_timeout_falls_back_to_template(monkeypatch):
    import asyncio
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")
    monkeypatch.setenv("ASK_TIMEOUT_S", "0.05")

    async def slow(system, prompt, *a, **kw):
        await asyncio.sleep(5)
        return "late"
    monkeypatch.setattr(fast, "gemini_once", slow)
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", "lat": 29.7, "lon": -95.4}).json()
    assert j["generated_by"] == "template" and j["warnings"] and "timed out" in j["warnings"][0]
    assert j["answer"] and "sources" in j and "tools_used" in j


def test_ask_gemini_single_call(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def ok(system, prompt, *a, **kw):
        return "It flooded in Harvey. Not official guidance."
    monkeypatch.setattr(fast, "gemini_once", ok)
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", "lat": 29.7, "lon": -95.4}).json()
    assert j["generated_by"] == "gemini" and "warnings" not in j
