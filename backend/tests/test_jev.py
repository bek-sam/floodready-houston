"""Jev decision layer (TypeSafe System One): httpx mocked at the boundary, no network, no real keys."""
import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from sqlalchemy import create_engine, inspect, text

from app.ai import config as aicfg
from app.ai import decide, fast, graph, rag, routing
from app.ai.router import router
from app.db import _add_missing_columns as add_columns
from app.services import report_check, route

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)
GOOD = "https://example.org/good"
LOC = {"lat": 29.7, "lon": -95.4}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    decide._cache.clear()
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    for k in ("JEV_ENABLED", "JEV_TIMEOUT", "JEV_MIN_CONF", "JEV_NON_EN", "JEV_AGENT_ROUTE", "JEV_GUARD", "TYPESAFE_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(rag, "search", lambda q, k=4: [
        {"kind": "fact", "file": "x.md", "title": "T", "text": "Flood insurance takes 30 days.", "source": GOOD, "score": 1}])

    async def fake_tool(name, args):
        return {"ok": name, "source": GOOD}
    monkeypatch.setattr(fast, "run_tool", fake_tool)
    monkeypatch.setattr(graph, "run_tool", fake_tool)


class Resp:
    def __init__(self, status=200, body=None, raw=None):
        self.status_code, self.body, self.raw = status, body, raw

    def json(self):
        if self.raw is not None:
            return json.loads(self.raw)
        return self.body


def mock_jev(monkeypatch, responder, key="fake-ts"):
    """responder(request_json) -> Resp | Exception | coroutine. Returns the list of request bodies."""
    monkeypatch.setenv("TYPESAFE_API_KEY", key)
    sent = []

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            assert url == decide.API and headers["Authorization"] == f"Bearer {key}"
            sent.append(json)
            r = responder(json)
            if asyncio.iscoroutine(r):
                r = await r
            if isinstance(r, Exception):
                raise r
            return r
    monkeypatch.setattr(decide.httpx, "AsyncClient", FakeClient)
    return sent


def answers(intent=None, conf=0.9, danger=0.0, complexity=None, cconf=0.9, tools=None, guard=None):
    """A responder that answers whichever questions were asked."""
    def r(req):
        out = {}
        for k in req["questions"]:
            if k == "intent" and intent:
                out[k] = {"type": "choice", "choice": intent, "confidence": conf, "probabilities": {intent: conf}}
            elif k == "danger":
                out[k] = {"type": "noul", "noul": danger}
            elif k == "complexity" and complexity is not None:
                p = {str(i): (cconf if i == complexity else (1 - cconf) / 2) for i in range(3)}
                out[k] = {"type": "score", "score": complexity, "confidence": cconf, "legend": {}, "probabilities": p}
            elif k in decide.TOOL_Q:
                out[k] = {"type": "noul", "noul": (tools or {}).get(k, 0.0)}
            elif k in decide.GUARD_Q:
                out[k] = {"type": "noul", "noul": (guard or {}).get(k, 0.0)}
        return Resp(body={"model": "jev-1.13.0", "answers": out, "usage": {}})
    return r


def state(q, lang="en", loc=True):
    s = {"question": q, "lang": lang, "history": [], **(LOC if loc else {"lat": None, "lon": None})}
    s.update(graph.classify_intent(s))
    return s


def strip(j):
    return {k: v for k, v in j.items() if k != "trace"}


# ---------- no key: identical behaviour ----------
def test_no_key_no_calls_and_same_answer(monkeypatch):
    sent = mock_jev(monkeypatch, lambda req: AssertionError("must not call"), key="")
    qs = ["Did my neighborhood flood before?", "My street is flooding, what do I do?", "How does flood insurance work?"]
    before = [strip(client.post("/api/ask", json={"question": q, **LOC}).json()) for q in qs]
    assert sent == [] and asyncio.run(decide.decide("x", "en", True)) is None
    assert asyncio.run(report_check.plausibility("flooded_road", 5, "water over road")) is None
    assert asyncio.run(decide.guard("drive through it", {})) == []
    monkeypatch.setenv("TYPESAFE_API_KEY", "fake-ts")
    monkeypatch.setenv("JEV_ENABLED", "0")  # key set but disabled: same answers, still no calls
    assert [strip(client.post("/api/ask", json={"question": q, **LOC}).json()) for q in qs] == before
    assert sent == []


def test_request_shape(monkeypatch):
    sent = mock_jev(monkeypatch, answers(intent="risk"))
    d = asyncio.run(decide.decide("Am I in a flood zone?", "en", True))
    req = sent[0]
    assert req["model"] == "jev-1.13.0" and isinstance(req["state"], dict) and req["state"]["question"] == "Am I in a flood zone?"
    q = req["questions"]
    assert q["intent"]["type"] == "choice" and list(q["intent"]["criteria"])[0] == "general"
    assert set(q["intent"]["criteria"]) == {n for n, _ in graph.INTENT_RULES} | {"general"}
    assert list(q["intent"]["criteria"])[1] not in decide.DANGER
    assert q["danger"]["type"] == "noul" and q["complexity"]["type"] == "score" and len(q["complexity"]["criteria"]) == 3
    assert set(decide.TOOL_Q) <= set(q) and set(decide.TOOL_Q) <= routing.LOC_TOOLS
    assert d.intent == "risk"
    asyncio.run(decide.decide("Am I in a flood zone?", "en", True))
    assert len(sent) == 1  # cached by normalized question + lang


# ---------- failures fall back ----------
def test_timeout_and_errors_fall_back(monkeypatch):
    async def slow(req):
        await asyncio.sleep(5)
    monkeypatch.setenv("JEV_TIMEOUT", "0.05")
    mock_jev(monkeypatch, slow)
    assert asyncio.run(decide.decide("Am I safe?", "en", True)) is None
    for status in (401, 422, 429, 529):
        decide._cache.clear()
        mock_jev(monkeypatch, lambda req, st=status: Resp(status=st, body={"error": "x"}))
        assert asyncio.run(decide.decide("Am I safe?", "en", True)) is None
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", **LOC}).json()
    assert j["answer"] and j["generated_by"] == "template"


def test_malformed_responses_do_not_crash(monkeypatch):
    bad = [Resp(raw="not json"), Resp(body={"answers": "x"}), Resp(body=[1, 2]), Resp(body={}),
           Resp(body={"answers": {"intent": {"choice": "bogus", "confidence": 2}, "danger": {"noul": "yes"},
                                  "complexity": {"probabilities": [1], "confidence": None}, "get_rain": {"noul": True},
                                  "unsafe_water": "high"}}),
           Resp(body={"answers": {"intent": None, "danger": None, "complexity": {"probabilities": {"9": 1}, "confidence": 0.9}}})]
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def ok(system, prompt, *a, **kw):
        return "Flood insurance takes 30 days [1]. Not official guidance."
    monkeypatch.setattr(fast, "gemini_once", ok)
    for b in bad:
        decide._cache.clear()
        mock_jev(monkeypatch, lambda req, b=b: b)
        d = asyncio.run(decide.decide("Will it rain?", "en", True))
        assert d is None or (d.intent is None and d.danger is None and d.complexity is None and d.tools == {})
        assert asyncio.run(decide.guard("Some answer.", {})) == []
        assert asyncio.run(report_check.plausibility("flooded_road", 5, "water")) is None
        j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", **LOC}).json()
        assert j["answer"]


# ---------- intent merge ----------
def test_confident_intent_overrides_regex_in_english(monkeypatch):
    s = state("What should I think about before hurricane season?")
    regex = list(s["intents"])
    mock_jev(monkeypatch, answers(intent="insurance", conf=0.9))
    asyncio.run(fast._apply_jev(s))
    assert regex != ["insurance"] and s["intents"] == ["insurance"] and s["intent"] == "insurance"
    decide._cache.clear()
    s = state("What should I think about before hurricane season?")
    mock_jev(monkeypatch, answers(intent="insurance", conf=0.5))  # not confident: regex kept
    asyncio.run(fast._apply_jev(s))
    assert s["intents"] == regex


def test_jev_cannot_remove_danger_but_can_add_it():
    d = decide.Decision(intent="general", intent_conf=0.99, danger=0.0)
    assert "street_flood" in decide.merge_intents(["street_flood"], d, "en")
    assert "emergency" in decide.merge_intents(["emergency", "driving"], d, "en")
    d = decide.Decision(intent="insurance", intent_conf=0.99, danger=0.8)
    assert decide.merge_intents(["insurance"], d, "en") == ["insurance", "emergency"]
    assert decide.merge_intents(["general"], decide.Decision(danger=0.6), "en") == ["emergency"]


def test_jev_danger_reaches_the_answer(monkeypatch):
    q = "the water is at my door and still going up fast"
    assert not set(state(q)["intents"]) & decide.DANGER  # the regex misses it
    mock_jev(monkeypatch, answers(intent="general", conf=0.4, danger=0.9))
    j = client.post("/api/ask", json={"question": q, **LOC}).json()
    assert "emergency" in j["trace"]["intent"] and "911" in j["answer"].split("\n")[0]


def test_non_english_stays_regex_first(monkeypatch):
    s = state("¿Cuánto cuesta el seguro de inundación?", lang="es")
    regex = list(s["intents"])
    mock_jev(monkeypatch, answers(intent="shelter", conf=0.99, danger=0.9))
    asyncio.run(fast._apply_jev(s))
    assert "shelter" not in s["intents"] and s["intents"] == [i for i in regex if i != "general"] + ["emergency"]
    monkeypatch.setenv("JEV_NON_EN", "1")
    decide._cache.clear()
    s = state("¿Cuánto cuesta el seguro de inundación?", lang="es")
    asyncio.run(fast._apply_jev(s))
    assert s["intents"][0] == "shelter"


# ---------- model + tools ----------
def test_complexity_drives_pick_model():
    strong, lite = aicfg.live(aicfg.complex_models())[0], fast.chat_model()
    s = state("Am I in a flood zone?")
    assert fast.pick_model(s) == lite  # heuristic: one intent, short
    s["jev"] = decide.Decision(complexity=2, complexity_conf=0.9)
    assert fast.pick_model(s) == strong
    long_multi = state("My policy and my flood zone and my route to work and shelters near me " * 3)
    assert fast.pick_model(long_multi) == strong
    long_multi["jev"] = decide.Decision(complexity=0, complexity_conf=0.9)
    assert fast.pick_model(long_multi) == lite
    long_multi["jev"] = decide.Decision(complexity=0, complexity_conf=0.3)  # unsure: heuristic
    assert fast.pick_model(long_multi) == strong


def test_tools_added_never_removed():
    s = state("Am I in a flood zone?")
    base = [n for n, _ in routing.select_tools(s)]
    s["jev"] = decide.Decision(tools={"get_rain": 0.9, "get_shelters": 0.59, "get_risk": 0.0, "get_alerts": 0.0,
                                      "get_flood_history": 0.7})
    names = [n for n, _ in routing.select_tools(s)]
    assert names[:len(base)] == base and "get_rain" in names and "get_flood_history" in names
    assert "get_shelters" not in names
    args = dict(routing.select_tools(s))
    assert args["get_flood_history"] == {**LOC, "zip": ""}
    s = state("How does flood insurance work?", loc=False)
    s["jev"] = decide.Decision(tools={"get_rain": 0.9})
    assert "get_rain" not in [n for n, _ in routing.select_tools(s)]  # no location: nothing to add


# ---------- guardrail ----------
def test_guardrail_replaces_unsafe_answer(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def unsafe(system, prompt, *a, **kw):
        return "You can drive through the water on your street, it is shallow. Not official guidance."
    monkeypatch.setattr(fast, "gemini_once", unsafe)
    sent = mock_jev(monkeypatch, answers(guard={"unsafe_water": 0.95}))
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", **LOC}).json()
    assert j["generated_by"] == "template" and "drive through the water" not in j["answer"]
    assert any("safety check" in w for w in j["warnings"])
    assert any("unsafe_water" in r["questions"] for r in sent)
    monkeypatch.setenv("JEV_GUARD", "0")
    decide._cache.clear()
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", **LOC}).json()
    assert j["generated_by"] == "gemini"


def test_guardrail_passes_safe_answer(monkeypatch):
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def ok(system, prompt, *a, **kw):
        return "Flood insurance takes 30 days [1]. Not official guidance."
    monkeypatch.setattr(fast, "gemini_once", ok)
    mock_jev(monkeypatch, answers(guard={"unsafe_water": 0.2}))
    j = client.post("/api/ask", json={"question": "Did my neighborhood flood before?", **LOC}).json()
    assert j["generated_by"] == "gemini"


# ---------- LangGraph tool loop route ----------
def _patch_llm(monkeypatch, replies):
    import langchain_google_genai as lg

    class FakeLLM:
        def bind_tools(self, tools):
            return self

        def invoke(self, msgs):
            return replies.pop(0)
    monkeypatch.setattr(lg, "ChatGoogleGenerativeAI", lambda **kw: FakeLLM())


def test_agent_route_runs_tool_loop(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gem")
    monkeypatch.setenv("JEV_AGENT_ROUTE", "1")
    calls = AIMessage(content="", tool_calls=[{"name": "insurance_countdown", "args": {"purchase_date": ""}, "id": "c1"}])
    final = AIMessage(content=f"Flood insurance takes 30 days, see {GOOD}. Not official guidance.")
    _patch_llm(monkeypatch, [calls, final])

    async def never(*a, **kw):
        raise AssertionError("single-call path must not run")
    monkeypatch.setattr(fast, "gemini_once", never)
    mock_jev(monkeypatch, answers(intent="insurance", complexity=2, cconf=0.9))
    j = client.post("/api/ask", json={"question": "Plan my insurance, route and shelter for the storm", **LOC}).json()
    assert j["generated_by"] == "gemini" and j["tools_used"] == ["insurance_countdown"]
    assert "30 days" in j["answer"] and j["trace"]["route"] == "graph"


def test_agent_route_off_by_default(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gem")
    _patch_llm(monkeypatch, [])  # would raise IndexError if the tool loop ran

    async def ok(system, prompt, *a, **kw):
        return "Flood insurance takes 30 days [1]. Not official guidance."
    monkeypatch.setattr(fast, "gemini_once", ok)
    mock_jev(monkeypatch, answers(intent="insurance", complexity=2, cconf=0.9))
    j = client.post("/api/ask", json={"question": "Plan my insurance, route and shelter for the storm", **LOC}).json()
    assert j["generated_by"] == "gemini" and j["trace"]["route"] == "prefetch"


# ---------- community reports ----------
def test_report_plausibility_stored(monkeypatch):
    from app.main import app as main_app
    from fastapi.testclient import TestClient as TC
    with TC(main_app) as c:
        mock_jev(monkeypatch, lambda req: Resp(body={"answers": {
            "real": {"type": "noul", "noul": 0.2}, "spam": {"type": "noul", "noul": 0.9},
            "severity": {"type": "score", "score": 0, "confidence": 0.8, "legend": {}, "probabilities": {"0": 0.8}}}}))
        r = c.post("/api/reports", json={**LOC, "kind": "flooded_road", "note": "lol my cat is a boat"}).json()
        r2 = c.post("/api/reports", json={**LOC, "kind": "flooded_road"}).json()  # no note: not checked
    from app.db import Report, get_session
    with get_session() as s:
        assert s.query(Report).filter(Report.id == r["id"]).first().plausibility == 0.02
        assert s.query(Report).filter(Report.id == r2["id"]).first().plausibility is None
        s.query(Report).filter(Report.id.in_([r["id"], r2["id"]])).delete()
        s.commit()


def test_add_columns_upgrades_old_sqlite(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/old.db")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE reports (id VARCHAR(32), created_at DATETIME, lat FLOAT, lon FLOAT, kind VARCHAR(40), "
                       "depth_in FLOAT, note VARCHAR(1000))"))
    add_columns(eng)
    add_columns(eng)  # idempotent
    assert "plausibility" in {c["name"] for c in inspect(eng).get_columns("reports")}


def _route_with_reports(monkeypatch, reports):
    monkeypatch.setattr(route, "load_crossings", lambda: [])
    monkeypatch.setattr(route, "recent_reports", lambda: reports)

    async def osrm(*a, **k):
        return {"routes": [{"geometry": {"type": "LineString", "coordinates": [[-95.1, 29.0], [-95.0, 29.0], [-94.95, 29.0], [-94.9, 29.0]]}}]}

    async def none(*a, **k):
        return {"alerts": []}

    async def empty(*a, **k):
        return []
    monkeypatch.setattr(route, "get_json", osrm)
    monkeypatch.setattr(route.diskcache, "get", lambda *a: None)
    monkeypatch.setattr(route.diskcache, "put", lambda *a: None)
    monkeypatch.setattr(route, "get_alerts", none)
    monkeypatch.setattr(route, "route_warnings", empty)
    monkeypatch.setattr(route, "nearest_gauges", empty)
    return asyncio.run(route.check_route({"lat": 29.0, "lon": -95.1}, {"lat": 29.0, "lon": -94.9}))


def test_route_ignores_implausible_reports_for_avoid(monkeypatch):
    rep = {"kind": "flooded_road", "depth_in": 12, "note": "deep", "created_at": "2026-10-11T00:00:00+00:00",
           "confirms": 0, "clears": 0, "lat": 29.0}
    two = [{**rep, "id": "a", "lon": -95.0, "plausibility": None}, {**rep, "id": "b", "lon": -94.95, "plausibility": None}]
    assert _route_with_reports(monkeypatch, two)["verdict"] == "avoid"  # null = no Jev: unchanged
    two[1]["plausibility"] = 0.1
    r = _route_with_reports(monkeypatch, two)
    assert r["verdict"] != "avoid" and r["report_count"] == 2  # still shown, just not counted
    two[1]["plausibility"] = 0.8
    assert _route_with_reports(monkeypatch, two)["verdict"] == "avoid"


def test_stream_uses_jev_and_guard_only_logs(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(fast, "gemini_key", lambda: "k")

    async def fake(system, prompt, model=None):
        yield "Flood insurance takes 30 days. "
    monkeypatch.setattr(fast, "gemini_stream", fake)
    sent = mock_jev(monkeypatch, answers(intent="insurance", conf=0.9, guard={"unsafe_water": 0.9}))
    r = client.post("/api/ask/stream", json={"question": "What should I think about before hurricane season?", **LOC})
    ev = [json.loads(b[6:]) for b in r.text.split("\n\n") if b.startswith("data: ")]
    assert ev[-1]["type"] == "final" and ev[-1]["generated_by"] == "gemini"  # streaming is never blocked
    assert ev[-1]["trace"]["intent"] == "insurance" and "intent" in sent[0]["questions"]
