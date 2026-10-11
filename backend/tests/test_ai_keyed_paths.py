"""Keyed AI paths with SDK clients mocked at their boundary (no network, no real keys)."""
import json
import os
import sys
import tempfile
import types as pytypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/t.db")

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402

from app.ai import graph, memory, plan, rag, voice  # noqa: E402
from app.ai.router import router  # noqa: E402

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)
GOOD_URL = "https://example.org/good"


@pytest.fixture(autouse=True)
def keys(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gem")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-el")
    monkeypatch.setenv("BACKBOARD_API_KEY", "")
    monkeypatch.setattr(voice, "CACHE", tmp_path / "voice")
    monkeypatch.setattr(graph, "rag", rag)
    monkeypatch.setattr(graph.rag, "search", lambda q, k=4: [
        {"kind": "fact", "file": "x.md", "title": "T", "text": "Flood insurance takes 30 days.", "source": GOOD_URL, "score": 1}])


class FakeLLM:
    def __init__(self, replies, log):
        self.replies, self.log = list(replies), log

    def bind_tools(self, tools):
        self.log.append(("tools", [t.name for t in tools]))
        return self

    def invoke(self, msgs):
        self.log.append(("invoke", len(msgs)))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def patch_llm(monkeypatch, replies, models=None):
    log = []
    import langchain_google_genai as lg

    def factory(**kw):
        log.append(("init", kw["model"], kw["google_api_key"]))
        if models is not None:
            return FakeLLM(models.pop(0) if models else [], log)
        return FakeLLM(replies, log)
    monkeypatch.setattr(lg, "ChatGoogleGenerativeAI", factory)
    return log


def gask(body: dict) -> dict:
    """The LangGraph tool-calling agent (graph.ask). /api/ask itself now uses the single-call fast path."""
    import asyncio
    return asyncio.run(graph.ask(body["question"], body.get("lang", "en"), body.get("lat"), body.get("lon"),
                                 body.get("history"), body.get("mode")))


def test_ask_tool_round_trip_and_citation_filter(monkeypatch):
    calls = AIMessage(content="", tool_calls=[{"name": "insurance_countdown", "args": {"purchase_date": ""}, "id": "c1"}])
    final = AIMessage(content=f"Wait 30 days. See {GOOD_URL}, and made-up https://evil.example/fake. Not official guidance.")
    log = patch_llm(monkeypatch, [calls, final])
    j = gask({"question": "Where is the nearest shelter?"})
    assert j["generated_by"] == "gemini"
    assert j["tools_used"] == ["insurance_countdown"]
    assert j["sources"] == [GOOD_URL]
    assert "evil.example" not in j["answer"]
    assert ("init", "gemini-2.5-flash", "fake-gem") in log and log[1][0] == "tools"


def test_ask_list_content_blocks_and_emergency_911(monkeypatch):
    patch_llm(monkeypatch, [AIMessage(content=[{"type": "text", "text": "Stay high."}, {"type": "thinking", "thinking": "x"}])])
    j = gask({"question": "I am trapped, rescue me"})
    assert j["generated_by"] == "gemini" and j["answer"].startswith("Call 911.")


def test_ask_tool_limit_does_not_loop_forever(monkeypatch):
    loop = [AIMessage(content="", tool_calls=[{"name": "nope", "args": {}, "id": f"i{i}"}]) for i in range(10)]
    patch_llm(monkeypatch, loop)
    j = gask({"question": "hello"})
    assert j["generated_by"] == "template" and "official guidance" in j["answer"].lower()


@pytest.mark.parametrize("exc", [RuntimeError("boom"), ConnectionError("net"), ValueError("PERMISSION_DENIED 403")])
def test_ask_llm_errors_fall_back_to_template(monkeypatch, exc):
    patch_llm(monkeypatch, [exc])
    assert gask({"question": "Is there a waiting period for flood insurance?"})["generated_by"] == "template"


def test_ask_model_not_found_tries_next_model(monkeypatch):
    log = patch_llm(monkeypatch, None, models=[[RuntimeError("404 NOT_FOUND: models/gemini-old is not found")], [AIMessage(content="ok answer")]])
    monkeypatch.setenv("GEMINI_MODEL", "gemini-old")
    j = gask({"question": "Where is the nearest shelter?"})
    assert j["generated_by"] == "gemini"
    from app.ai.config import FALLBACK_MODELS
    assert [e[1] for e in log if e[0] == "init"][:2] == ["gemini-old", FALLBACK_MODELS[0]]


def test_ask_all_models_missing_falls_back(monkeypatch):
    err = lambda: [RuntimeError("404 model not found")]  # noqa: E731
    patch_llm(monkeypatch, None, models=[err(), err(), err(), err()])
    assert gask({"question": "flood insurance waiting period"})["generated_by"] == "template"


def test_ask_empty_model_answer_falls_back(monkeypatch):
    patch_llm(monkeypatch, [AIMessage(content="")])
    assert gask({"question": "hello"})["generated_by"] == "template"


def test_ask_graph_crash_is_not_500(monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(graph, "ask", boom)
    r = client.post("/api/ask", json={"question": "hi"})
    assert r.status_code == 200 and "911" in r.json()["answer"]


# ---- /plan ----
def patch_genai(monkeypatch, behaviours):
    """behaviours: list of str (response text) or Exception, consumed per generate_content call."""
    from google import genai
    seen = []

    class Models:
        def generate_content(self, *, model, contents, config=None):
            seen.append(model)
            b = behaviours.pop(0)
            if isinstance(b, Exception):
                raise b
            return pytypes.SimpleNamespace(text=b)

    monkeypatch.setattr(genai, "Client", lambda api_key=None: pytypes.SimpleNamespace(models=Models()))
    return seen


def test_plan_gemini_json(monkeypatch):
    steps = [{"title": "A", "detail": "d", "when": "bogus"}, {"title": "B", "detail": "e", "when": "storm"}, {"nope": 1}]
    patch_genai(monkeypatch, ["```json\n" + json.dumps(steps) + "\n```"])
    j = client.post("/api/plan", json={"profile": {}}).json()
    assert j["generated_by"] == "gemini"
    assert [s["when"] for s in j["steps"]] == ["now", "storm"]


def test_plan_wrapped_object(monkeypatch):
    patch_genai(monkeypatch, [json.dumps({"steps": [{"title": "A", "detail": "d", "when": "now"}]})])
    assert client.post("/api/plan", json={"profile": {}}).json()["generated_by"] == "gemini"


@pytest.mark.parametrize("bad", ["not json {", "[]", "null", "42", "", '[{"title": 1}]', "[1,2]"])
def test_plan_malformed_json_falls_back(monkeypatch, bad):
    patch_genai(monkeypatch, [bad])
    j = client.post("/api/plan", json={"profile": {"renter": True}}).json()
    assert j["generated_by"] == "template" and len(j["steps"]) >= 5


def test_plan_sdk_error_and_model_not_found(monkeypatch):
    patch_genai(monkeypatch, [RuntimeError("quota")])
    assert client.post("/api/plan", json={"profile": {}}).json()["generated_by"] == "template"
    seen = patch_genai(monkeypatch, [RuntimeError("404 NOT_FOUND model"), json.dumps([{"title": "A", "detail": "d", "when": "now"}])])
    assert client.post("/api/plan", json={"profile": {}}).json()["generated_by"] == "gemini"
    assert len(seen) == 2 and seen[0] != seen[1] or seen[0] == "gemini-2.5-flash"


# ---- /voice ----
def patch_eleven(monkeypatch, chunks=(b"ID3", b"audio"), exc=None):
    import elevenlabs.client as ec
    calls = []

    class TTS:
        def convert(self, **kw):
            calls.append(kw)
            if exc:
                raise exc
            return iter(chunks)

    monkeypatch.setattr(ec, "ElevenLabs", lambda api_key=None: pytypes.SimpleNamespace(text_to_speech=TTS()))
    return calls


def test_voice_bytes_and_cache(monkeypatch):
    calls = patch_eleven(monkeypatch)
    r = client.post("/api/voice", json={"text": "Hello", "lang": "en"})
    assert r.status_code == 200 and r.content == b"ID3audio" and r.headers["content-type"] == "audio/mpeg"
    assert calls[0]["voice_id"] and calls[0]["model_id"] and calls[0]["text"] == "Hello"
    r2 = client.post("/api/voice", json={"text": "Hello", "lang": "en"})
    assert r2.content == b"ID3audio" and len(calls) == 1
    client.post("/api/voice", json={"text": "Hello", "lang": "es"})
    assert len(calls) == 2


def test_voice_errors_503(monkeypatch):
    patch_eleven(monkeypatch, exc=RuntimeError("401"))
    assert client.post("/api/voice", json={"text": "x"}).status_code == 503
    patch_eleven(monkeypatch, chunks=())
    r = client.post("/api/voice", json={"text": "empty"})
    assert r.status_code == 503  # empty audio must not be served as mp3


# ---- embeddings ----
def test_embeddings_batch_cache_and_failure(monkeypatch, tmp_path):
    from google import genai
    calls = []

    class Models:
        def embed_content(self, *, model, contents, config=None):
            calls.append((model, len(contents), config.output_dimensionality))
            return pytypes.SimpleNamespace(embeddings=[pytypes.SimpleNamespace(values=[1.0] + [0.0] * 767) for _ in contents])

    monkeypatch.setattr(genai, "Client", lambda api_key=None: pytypes.SimpleNamespace(models=Models()))
    monkeypatch.setattr(rag, "BACKEND", tmp_path)
    chunks = [{"title": f"t{i}", "text": f"text {i}"} for i in range(100)]
    v = rag._cached_embeddings(chunks)
    assert v.shape == (100, 768) and [c[1] for c in calls] == [90, 10] and calls[0][2] == 768
    assert np.allclose(np.linalg.norm(v, axis=1), 1)
    v2 = rag._cached_embeddings(chunks)
    assert len(calls) == 2 and v2.shape == v.shape  # second call came from disk

    class Boom:
        def embed_content(self, **kw):
            raise RuntimeError("404 model not found")
    monkeypatch.setattr(genai, "Client", lambda api_key=None: pytypes.SimpleNamespace(models=Boom()))
    assert rag._embed(["a"]) is None
    assert rag._embed([]) is None


def test_hybrid_search_uses_vectors(monkeypatch):
    chunks = [{"title": "a", "text": "flood insurance wait", "source": "https://s/1", "file": "k.md", "kind": "fact"},
              {"title": "b", "text": "go bag water", "source": "https://s/2", "file": "k.md", "kind": "fact"}]
    monkeypatch.setattr(rag, "_cached_embeddings", lambda c: np.eye(2, dtype=np.float32))
    monkeypatch.setattr(rag, "_embed", lambda t: np.array([[0.0, 1.0]], dtype=np.float32))
    idx = rag.Index(chunks)
    hits = idx.search("flood go", 2)
    assert hits and hits[0]["source"] == "https://s/2"


# ---- Backboard ----
def test_backboard_flow_and_errors(monkeypatch):
    import httpx
    monkeypatch.setenv("BACKBOARD_API_KEY", "bb")
    seen = []

    def handler(req: httpx.Request):
        seen.append((req.method, req.url.path, req.headers.get("x-api-key")))
        if req.url.path.endswith("/assistants"):
            return httpx.Response(200, json={"assistant_id": "A1"})
        if req.url.path.endswith("/threads"):
            return httpx.Response(200, json={"thread_id": "T1"})
        return httpx.Response(200, json={})

    real = httpx.Client
    monkeypatch.setattr(memory.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    assert memory._backboard_sync({"id": "abcdefghijk"}, None) == "A1"
    assert [s[1] for s in seen] == ["/api/assistants", "/api/assistants/A1/threads", "/api/threads/T1/messages"]
    assert all(s[2] == "bb" for s in seen)

    monkeypatch.setattr(memory.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(lambda r: httpx.Response(500)), **kw))
    assert memory._backboard_sync({"id": "abcdefghijk"}, None) is None  # swallowed, no raise
    p = memory.save_profile({"name": "x"})  # still saves locally
    assert memory.get_profile(p["id"])["name"] == "x"


def test_ask_voice_speak_and_history_with_gemini(monkeypatch):
    final = AIMessage(content="Move to higher ground. Not official guidance.\nSPEAK: Move to higher ground now. Visit https://x.org **today**. \U0001F30A")
    patch_llm(monkeypatch, [final])
    hist = [{"role": "user", "content": "My mom needs dialysis"}, {"role": "assistant", "content": "Call her center."}]
    j = gask({"question": "What if the power goes out?", "mode": "voice", "history": hist})
    assert "SPEAK" not in j["answer"]
    assert "http" not in j["speak"] and "*" not in j["speak"] and "\U0001F30A" not in j["speak"] and len(j["speak"]) <= 350
    assert j["speak"].startswith("Move to higher ground")
