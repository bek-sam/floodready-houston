"""'How I answered' trace on /ask and /ask/stream final (no keys, no network)."""
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import rag, tools
from app.ai.tools import TOOL_SOURCE
from app.ai.router import router

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)
GOOD = "https://example.org/good"
KEYS = {"intent", "route", "cache_hit", "retrieved", "tools", "answer", "total_ms"}


def _patch(monkeypatch):
    async def fake(name, args):
        return {"ok": name, "source": GOOD}
    monkeypatch.setattr(tools, "_run_tool", fake)
    monkeypatch.setattr(rag, "search", lambda q, k=4: (
        rag._trace.add_retrieved([{"title": "T", "source": GOOD, "score": 1}]) or
        [{"kind": "fact", "file": "x.md", "title": "T", "text": "Flood insurance takes 30 days.", "source": GOOD, "score": 1}]))


def _check(t):
    assert KEYS <= set(t)
    assert t["answer"]["by"] == "template" and isinstance(t["answer"]["ms"], int)
    assert t["tools"] and {"name", "ms", "source"} <= set(t["tools"][0]) and t["tools"][0]["source"] == TOOL_SOURCE[t["tools"][0]["name"]]
    assert t["retrieved"][0]["source"].startswith("http") and len(t["retrieved"]) <= 3


def test_ask_trace_template(monkeypatch):
    _patch(monkeypatch)
    r = client.post("/api/ask", json={"question": "Is 77096 at flood risk?", "lang": "en", "lat": 29.69, "lon": -95.49}).json()
    assert r["generated_by"] == "template" and "tools_used" in r
    _check(r["trace"])


def test_stream_final_trace(monkeypatch):
    _patch(monkeypatch)
    r = client.post("/api/ask/stream", json={"question": "Did my neighborhood flood before?", "lat": 29.7, "lon": -95.4})
    ev = [json.loads(b[6:]) for b in r.text.split("\n\n") if b.startswith("data: ")]
    fin = [e for e in ev if e["type"] == "final"][0]
    assert "timings" in fin
    _check(fin["trace"])
