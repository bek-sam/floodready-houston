import asyncio
import base64
import json
import time
from types import SimpleNamespace as NS

from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.genai import types

from app.ai import live, live_router


def _app():
    a = FastAPI()
    a.include_router(live_router.router)
    return a


def msg(**kw):
    base = dict(server_content=None, tool_call=None, go_away=None, session_resumption_update=None,
                voice_activity=None, tool_call_cancellation=None)
    base.update(kw)
    return NS(**base)


def sc(**kw):
    base = dict(interrupted=False, input_transcription=None, output_transcription=None, model_turn=None,
                turn_complete=False)
    base.update(kw)
    return NS(**base)


def test_no_key_sends_error_and_closes(monkeypatch):
    monkeypatch.setattr(live, "make_client", lambda: None)
    with TestClient(_app()).websocket_connect("/live") as ws:
        assert ws.receive_json()["type"] == "error"


def test_models_and_prompt(monkeypatch):
    monkeypatch.delenv("GEMINI_LIVE_MODEL", raising=False)
    assert live.live_models() == ["gemini-3.8-live", "gemini-3.1-flash-live-preview", "gemini-2.5-flash-native-audio-latest"]
    p = live.system_prompt("es", 29.76, -95.37, context="- FEMA flood zone AE [FEMA NFHL]")
    assert "Spanish" in p and "911" in p and "29.76000" in p
    assert "SESSION CONTEXT" in p and "zone AE" in p and "switch" in p and "Never invent numbers" in p
    assert "Let me check" in live.system_prompt("en", non_blocking=False)
    assert {d.name for d in live.tool_declarations()} == {
        "get_risk", "get_flood_history", "get_zip_insurance", "get_alerts", "get_medical", "check_route", "search_knowledge"}


def test_execute_tool_unknown():
    assert asyncio.run(live.execute_tool("nope", {})) == {"error": "unknown tool"}


def test_build_config_auto_vad_and_features(monkeypatch):
    for k in ("LIVE_VAD_SILENCE_MS", "LIVE_VAD_PREFIX_MS", "LIVE_VAD_END_SENSITIVITY", "LIVE_NON_BLOCKING", "LIVE_AFFECTIVE"):
        monkeypatch.delenv(k, raising=False)
    c = live.build_config("en", 29.7, -95.3, context="- x", resume_handle="h1", model="gemini-3.8-live")
    aad = c.realtime_input_config.automatic_activity_detection
    assert aad.disabled is False and aad.silence_duration_ms == 600 and aad.prefix_padding_ms == 200
    assert aad.end_of_speech_sensitivity == types.EndSensitivity.END_SENSITIVITY_HIGH
    assert c.session_resumption.handle == "h1"
    assert c.context_window_compression.sliding_window.target_tokens > 0
    assert c.input_audio_transcription is not None and c.output_audio_transcription is not None
    assert all(d.behavior == types.Behavior.NON_BLOCKING for d in c.tools[0].function_declarations)
    assert c.enable_affective_dialog is None and c.proactivity is None
    assert live.build_config("en", None, None, model="gemini-2.5-flash-native-audio-latest").enable_affective_dialog is True

    monkeypatch.setenv("LIVE_VAD_SILENCE_MS", "500")
    monkeypatch.setenv("LIVE_VAD_END_SENSITIVITY", "low")
    monkeypatch.setenv("LIVE_NON_BLOCKING", "0")
    c = live.build_config("en", None, None, model="gemini-3.8-live")
    aad = c.realtime_input_config.automatic_activity_detection
    assert aad.silence_duration_ms == 500 and aad.end_of_speech_sensitivity == types.EndSensitivity.END_SENSITIVITY_LOW
    assert c.tools[0].function_declarations[0].behavior is None
    assert "Let me check" in c.system_instruction

    m = live.build_config("en", None, None, manual=True)
    assert m.realtime_input_config.automatic_activity_detection.disabled is True


def test_function_response_scheduling():
    r = live.function_response("1", "get_risk", {"a": 1}, True)
    assert r.scheduling == types.FunctionResponseScheduling.WHEN_IDLE and r.response == {"output": {"a": 1}}
    assert live.function_response("2", "get_alerts", {}, True).scheduling == types.FunctionResponseScheduling.INTERRUPT
    assert live.function_response("3", "get_risk", {"error": "x"}, False).scheduling is None


def test_decode_profile():
    raw = base64.urlsafe_b64encode(json.dumps({"zip": "77096", "pets": True}).encode()).decode().rstrip("=")
    assert live.decode_profile(raw) == {"zip": "77096", "pets": True}
    assert live.decode_profile("!!notb64") is None and live.decode_profile(None) is None


def test_build_context_parallel_with_budget(monkeypatch):
    calls = []

    async def fake_run(name, args):
        calls.append((name, args))
        if name == "get_alerts":
            await asyncio.sleep(5)  # exceeds budget -> dropped
        return {
            "get_risk": {"fema_zone": "AE", "sfha": True, "elevation_ft": 40, "harvey": {"flooded": True, "source": "https://x.gov/a"},
                         "nearest_gauges": [{"name": "Brays", "stage_ft": 9, "status": "normal", "flood_stages": {"minor": 41}}]},
            "get_flood_history": {"events": [{"name": "Hurricane Harvey", "start": "2017-08-25",
                                              "nearest_gauge": {"name": "Brays", "distance_mi": 1, "peak_ft": 44, "peak_category": "major"}}]},
            "get_zip_insurance": {"zip": "77096", "claims": {"total": 900, "since_2017": 300, "by_year": [{"year": 2017, "count": 250}]}},
        }.get(name, {"error": "x"})

    monkeypatch.setattr(live.ai_tools, "run_tool", fake_run)
    live._CACHE.clear()
    t = time.monotonic()
    ctx = asyncio.run(live.build_context(29.7, -95.4, "Meyerland, Houston, TX 77096", {"pets": True, "name": "Ann"}, budget=0.3))
    assert time.monotonic() - t < 1.5
    assert {c[0] for c in calls} == {"get_risk", "get_flood_history", "get_alerts", "get_zip_insurance"}
    assert "zone AE" in ctx and "Harvey" in ctx and "900 NFIP" in ctx and "[OpenFEMA NFIP]" in ctx
    assert "pets=true" in ctx and "Ann" not in ctx and "Not preloaded" in ctx and "alerts" in ctx
    assert asyncio.run(live.build_context(None, None)) == ""
    # completed fetches are cached: a second session reuses them without calling the tool again
    calls.clear()
    ctx2 = asyncio.run(live.build_context(29.7, -95.4, "TX 77096", None, budget=0.3))
    assert "zone AE" in ctx2 and "get_risk" not in {c[0] for c in calls}
    live._CACHE.clear()


class FakeSession:
    def __init__(self, script=None):
        self.sent, self.tool_resp = [], None
        self.turn = 0
        self.script = script or []

    async def send_realtime_input(self, **kw):
        self.sent.append(kw)

    async def send_tool_response(self, **kw):
        self.tool_resp = kw

    async def receive(self):
        self.turn += 1
        if self.turn == 1:
            for m in self.script:
                yield m
        else:
            await asyncio.sleep(10)


def _patch(monkeypatch, sessions, connects):
    monkeypatch.setattr(live, "make_client", lambda: object())

    async def fake_ctx(lat, lon, place=None, profile=None, budget=1.5):
        return "- ctx"

    async def fake_connect(stack, client, lang, lat, lon, **kw):
        connects.append(kw)
        return sessions.pop(0), "gemini-3.8-live"

    async def fake_tool(name, args):
        return {"ok": True}

    monkeypatch.setattr(live, "build_context", fake_ctx)
    monkeypatch.setattr(live, "connect_with_fallback", fake_connect)
    monkeypatch.setattr(live, "execute_tool", fake_tool)


def _collect(ws, n):
    got = [ws.receive() for _ in range(n)]
    return [json.loads(g["text"]) for g in got if g.get("text")], [g["bytes"] for g in got if g.get("bytes")]


def test_bridge(monkeypatch):
    script = [
        msg(session_resumption_update=NS(new_handle="H1", resumable=True)),
        msg(server_content=sc(input_transcription=NS(text="is my ", finished=False))),
        msg(server_content=sc(input_transcription=NS(text="house safe", finished=True))),
        msg(tool_call=NS(function_calls=[NS(id="1", name="get_zip_insurance", args={"zip": "77002"})])),
        msg(server_content=sc(turn_complete=True)),  # silent turn after a NON_BLOCKING call -> no model_end
        msg(server_content=sc(output_transcription=NS(text="yes", finished=False),
                              model_turn=NS(parts=[NS(inline_data=NS(data=b"\x01\x02"))]))),
        msg(server_content=sc(turn_complete=True)),
        msg(server_content=sc(interrupted=True)),
    ]
    fs = FakeSession(script)
    connects = []
    _patch(monkeypatch, [fs], connects)
    with TestClient(_app()).websocket_connect("/live?lang=en&lat=29.7&lon=-95.3&place=Houston") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready" and ready["model"] == "gemini-3.8-live" and ready["mode"] == "auto"
        ws.send_bytes(b"\x00\x00" * 160)
        texts, audio = _collect(ws, 16)
        assert {"type": "resume", "handle": "H1"} in texts
        caps = [t for t in texts if t["type"] == "caption"]
        assert {"type": "caption", "role": "user", "text": "is my house safe", "delta": "house safe", "final": True} in caps
        assert any(c["role"] == "model" and c["text"] == "yes" and c["final"] for c in caps)
        assert {"type": "transcript", "role": "user", "text": "is my "} in texts
        assert {"type": "tool", "name": "get_zip_insurance"} in texts
        assert {"type": "thinking", "label": "Checking insurance claims"} in texts
        assert {"type": "interrupted"} in texts
        turns = [t["event"] for t in texts if t["type"] == "turn"]
        assert turns == ["user_end", "model_start", "model_end"]
        assert all(isinstance(t["t"], int) for t in texts if t["type"] == "turn")
        assert audio == [b"\x01\x02"]
        ws.send_text(json.dumps({"type": "end"}))
    assert fs.sent[0]["audio"].mime_type == "audio/pcm;rate=16000"
    r = fs.tool_resp["function_responses"][0]
    assert r.name == "get_zip_insurance" and r.scheduling == types.FunctionResponseScheduling.WHEN_IDLE
    assert connects[0]["context"] == "- ctx" and connects[0]["manual"] is False


def test_ptt_switches_to_manual(monkeypatch):
    s1, s2 = FakeSession([msg(session_resumption_update=NS(new_handle="H9", resumable=True))]), FakeSession()
    connects = []
    _patch(monkeypatch, [s1, s2], connects)
    with TestClient(_app()).websocket_connect("/live?lang=es") as ws:
        assert ws.receive_json()["type"] == "ready"
        assert ws.receive_json() == {"type": "resume", "handle": "H9"}
        ws.send_text(json.dumps({"type": "ptt", "down": True}))
        ws.send_bytes(b"\x05\x00" * 10)
        ws.send_text(json.dumps({"type": "ptt", "down": False}))
        ev = ws.receive_json()
        assert ev["type"] == "turn" and ev["event"] == "user_end"
        ws.send_bytes(b"\x07\x00" * 10)  # outside PTT -> dropped
        ws.send_text(json.dumps({"type": "mute", "on": True}))
        ws.send_text(json.dumps({"type": "end"}))
    assert connects[1]["manual"] is True and connects[1]["resume_handle"] == "H9"
    kinds = [next(iter(k)) for k in s2.sent]
    assert kinds[:3] == ["activity_start", "audio", "activity_end"]
    assert not any(k.get("audio") and k["audio"].data.startswith(b"\x07") for k in s2.sent)


def test_ptt_query_starts_manual(monkeypatch):
    connects = []
    _patch(monkeypatch, [FakeSession()], connects)
    with TestClient(_app()).websocket_connect("/live?ptt=true&resume=abc") as ws:
        assert ws.receive_json()["mode"] == "ptt"
        ws.send_text(json.dumps({"type": "text", "text": "hola"}))
        assert ws.receive_json()["event"] == "user_end"
        ws.send_text(json.dumps({"type": "end"}))
    assert connects[0]["manual"] is True and connects[0]["resume_handle"] == "abc"
