"""AI fallback paths; must pass with no API keys."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for k in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "BACKBOARD_API_KEY"):
    os.environ[k] = ""
import tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai import plan, rag  # noqa: E402
from app.ai.router import router  # noqa: E402

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def test_chunks_have_sources():
    chunks = rag.load_chunks()
    assert chunks and all(c["source"] for c in chunks)


def test_bm25_search():
    hits = rag.search("flood insurance waiting period", 3)
    assert hits and {"text", "source", "score"} <= hits[0].keys()


def test_ask_fallback():
    r = client.post("/api/ask", json={"question": "Is there a waiting period for flood insurance?", "lang": "en"})
    j = r.json()
    assert r.status_code == 200 and j["generated_by"] == "template"
    assert "not official guidance" in j["answer"].lower() and isinstance(j["sources"], list)


def test_ask_emergency_and_tools_unavailable():
    j = client.post("/api/ask", json={"question": "I am trapped by rising water", "lat": 29.76, "lon": -95.37}).json()
    assert "911" in j["answer"]


def test_plan_template_covers_profile():
    p = {"language": "vi", "renter": True, "has_car": False, "pets": True, "mobility": "wheelchair", "medical": ["dialysis"]}
    j = client.post("/api/plan", json={"profile": p}).json()
    text = " ".join(s["title"] + s["detail"] for s in j["steps"]).lower()
    assert j["generated_by"] == "template"
    for word in ("dialysis", "mobility", "pets", "ride", "renter", "language"):
        assert word in text
    assert all(s["when"] in plan.WHEN for s in j["steps"])


def test_voice_503_without_key():
    assert client.post("/api/voice", json={"text": "hi", "lang": "en"}).status_code == 503


def test_profile_roundtrip():
    saved = client.post("/api/profile", json={"language": "en", "renter": True}).json()
    got = client.get(f"/api/profile/{saved['id']}", headers={"X-Profile-Token": saved["token"]}).json()
    assert got["renter"] is True
    assert client.get("/api/profile/nope").status_code == 404


def test_ask_vi_disclaimer_and_shelter_intent():
    j = client.post("/api/ask", json={"question": "Where is the nearest shelter?", "lang": "vi",
                                      "lat": 29.76, "lon": -95.37}).json()
    assert "911" in j["answer"] and "Đây không phải" in j["answer"]
    from app.ai.graph import classify_intent
    assert "shelter" in classify_intent({"question": "any pet friendly shelter?"})["intents"]


def test_gemini_sources_filtered():
    from app.ai.graph import answer_with_citations
    ctx = [{"source": "https://good.example/a", "text": "x", "title": "t"}]
    out = answer_with_citations({"question": "q", "lang": "en", "context": ctx, "generated_by": "gemini",
                                 "answer": "See https://evil.example/x and https://good.example/a."})
    assert out["sources"] == ["https://good.example/a"]


def test_scam_cue_and_shelter_tool_guard():
    from app.ai.tools import run_tool
    r = asyncio.run(run_tool("get_shelters", {"lat": 29.7, "lon": -95.3}))
    assert isinstance(r, dict)
    j = client.post("/api/ask", json={"question": "A contractor wants cash upfront", "lang": "en"}).json()
    assert "911" in j["answer"]


def test_shelter_answer_never_claims_open(monkeypatch):
    from app.ai.graph import _lead, Cites
    res = {"get_shelters": {"historical": True, "any_open": False, "source": "https://x.example/s",
                            "shelters": [{"name": "GRB", "status": "Open", "status_2017": "Open"}]}}
    text = " ".join(_lead({"tool_results": res}, Cites()))
    assert "don't have live shelter status" in text and "311" in text and "211" in text
    assert "nearest open" not in text.lower() and "(2017, historical)" in text


def test_spanish_question_gets_spanish_lead():
    j = client.post("/api/ask", json={"question": "¿Dónde puedo ir si no tengo carro y necesito diálisis?", "lang": "es"}).json()
    first = j["answer"].split("\n")[0]
    assert "Esto es lo más útil" in first or "911" in first
    assert "Esto no es una guía oficial" in j["answer"]
    assert "d: restructured" not in j["answer"]


def test_plan_has_no_ground_floor_safe_wording():
    p = {"language": "en", "mobility": "wheelchair", "has_car": False}
    for lang in ("en", "es", "vi"):
        j = client.post("/api/plan", json={"profile": {**p, "language": lang}}).json()
        assert "ground-floor-safe" not in " ".join(s["title"] + s["detail"] for s in j["steps"]).lower()
    es = client.post("/api/plan", json={"profile": {**p, "language": "es"}}).json()
    assert any("Plan de movilidad" == s["title"] for s in es["steps"])


def test_street_flood_pitch_questions():
    for q, lang in [("¿Qué hago si mi calle se inunda?", "es"), ("Que hago si mi calle se inunda", "es"),
                    ("What do I do if my street floods?", "en"), ("街道被淹了怎么办", "zh")]:
        j = client.post("/api/ask", json={"question": q, "lang": lang}).json()
        assert "911" in j["answer"] and j["sources"], q


def test_history_validation():
    from app.ai.graph import clean_history
    h = [{"role": "system", "content": "x"}, {"role": "user", "content": "a" * 900}] + \
        [{"role": "user", "content": f"q{i}"} for i in range(10)]
    out = clean_history(h)
    assert len(out) == 6 and all(t["role"] in ("user", "assistant") for t in out)
    assert len(clean_history([h[1]])[0]["content"]) == 600


def test_history_followup_intent():
    hist = [{"role": "user", "content": "My mom needs dialysis, what should we do before a storm?"},
            {"role": "assistant", "content": "Plan ahead with your dialysis center."}]
    r = client.post("/api/ask", json={"question": "What about her schedule?", "history": hist}).json()
    assert r["generated_by"] == "template" and "speak" not in r
    assert r["sources"]


def test_voice_speak_constraints():
    for q in ("Is there a waiting period for flood insurance?", "My street is flooding, what do I do?"):
        j = client.post("/api/ask", json={"question": q, "mode": "voice"}).json()
        sp = j["speak"]
        assert sp and len(sp) <= 350 and "http" not in sp and "[" not in sp and "*" not in sp
    assert "911" in j["speak"]
