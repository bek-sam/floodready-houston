"""AI endpoints. main.py mounts `router` under /api."""
import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from typing import Literal

from pydantic import BaseModel, Field

from . import fast, graph, memory, plan, telemetry, voice
from .tools import run_tool, warm

router = APIRouter()
_bg: set = set()


class AskBody(BaseModel):
    question: str
    lang: str = "en"
    lat: float | None = None
    lon: float | None = None
    history: list[dict[str, Any]] = []
    mode: str | None = None
    debug: bool = False  # eval only: include the evidence (chunks + compact tool data) the answer was built from


class PrefetchBody(BaseModel):
    lat: float
    lon: float


class FeedbackBody(BaseModel):
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=8000)
    rating: Literal[1, -1]
    lang: str = "en"


class PlanBody(BaseModel):
    profile: dict[str, Any] = {}
    lat: float | None = None
    lon: float | None = None


class VoiceBody(BaseModel):
    text: str
    lang: str = "en"


@router.post("/ask")
async def ask(body: AskBody):
    tr = telemetry.start("ask", body.question, body.lang)
    try:
        return await fast.ask_once(body.question, body.lang, body.lat, body.lon, body.history, body.mode,
                                   **({"debug": True} if body.debug else {}))
    except Exception:
        telemetry.set(route="error")
        return {"answer": "Sorry, I could not answer right now. In an emergency, Call 911. Not official guidance.",
                "sources": [], "generated_by": "template", "tools_used": [],
                **({"speak": "Sorry, I could not answer right now. In an emergency, call 911."} if body.mode == "voice" else {})}
    finally:
        telemetry.finish(tr)


@router.post("/ask/prefetch")
async def ask_prefetch(body: PrefetchBody):
    """Warm the location tool caches when the Ask page opens (runs in the background)."""
    task = asyncio.get_running_loop().create_task(warm(body.lat, body.lon))
    _bg.add(task)
    task.add_done_callback(_bg.discard)
    return {"status": "warming", "tools": ["get_risk", "get_flood_history", "get_alerts"]}


@router.post("/feedback")
async def feedback(body: FeedbackBody):
    try:
        fid = await run_in_threadpool(telemetry.save_feedback, body.question, body.answer, body.rating, body.lang)
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "feedback unavailable"}, status_code=503)
    return {"ok": True, "id": fid}


@router.post("/plan")
async def make_plan(body: PlanBody):
    risk = None
    if body.lat is not None and body.lon is not None:
        risk = await run_tool("get_risk", {"lat": body.lat, "lon": body.lon})
    return await run_in_threadpool(plan.make_plan, body.profile, risk)


@router.post("/voice")
async def make_voice(body: VoiceBody):
    if not voice.has_key():
        return JSONResponse({"error": "voice unavailable: no ELEVENLABS_API_KEY"}, status_code=503)
    try:
        audio = await run_in_threadpool(voice.synthesize, body.text, body.lang)
    except Exception:
        return JSONResponse({"error": "voice unavailable"}, status_code=503)
    return Response(audio, media_type="audio/mpeg")


@router.post("/profile")
async def save_profile(profile: dict[str, Any]):
    return await run_in_threadpool(memory.save_profile, profile)


@router.get("/profile/{profile_id}")
async def get_profile(profile_id: str):
    p = await run_in_threadpool(memory.get_profile, profile_id)
    if p is None:
        raise HTTPException(404, "profile not found")
    return p


async def _traced(gen, tr):
    """Re-enter the request's trace before each step (the stream may run in another task context)."""
    try:
        while True:
            telemetry._current.set(tr)
            try:
                chunk = await gen.__anext__()
            except StopAsyncIteration:
                break
            yield chunk
    finally:
        telemetry.finish(tr)


@router.post("/ask/stream")
async def ask_stream(body: AskBody):
    tr = telemetry.Trace("ask_stream", body.question, body.lang)
    return StreamingResponse(
        _traced(fast.stream_ask(body.question, body.lang, body.lat, body.lon, body.history, body.mode), tr),
        media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/voice/stream")
async def voice_stream(body: VoiceBody):
    if not voice.has_key():
        return JSONResponse({"error": "voice unavailable: no ELEVENLABS_API_KEY"}, status_code=503)
    gen = voice.stream_synthesize(body.text, body.lang)
    try:
        first = await run_in_threadpool(next, gen)  # fail fast with 503 before streaming starts
    except Exception:
        return JSONResponse({"error": "voice unavailable"}, status_code=503)

    async def body_iter():
        yield first
        while True:
            chunk = await run_in_threadpool(next, gen, None)
            if chunk is None:
                break
            yield chunk
    return StreamingResponse(body_iter(), media_type="audio/mpeg")


@router.get("/voice/filler")
async def voice_filler(lang: str = "en"):
    if not voice.has_key():
        return JSONResponse({"error": "voice unavailable: no ELEVENLABS_API_KEY"}, status_code=503)
    try:
        audio = await run_in_threadpool(voice.filler_audio, lang)
    except Exception:
        return JSONResponse({"error": "voice unavailable"}, status_code=503)
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=86400"})


@router.get("/ai/stats")
async def ai_stats(n: int = 100):
    """Aggregates over the last n AI requests (Demo mode). Costs are ESTIMATES from a static price table."""
    out = telemetry.stats(max(1, min(n, 1000)))
    try:
        out["feedback"] = await run_in_threadpool(telemetry.feedback_counts)
    except Exception:  # noqa: BLE001
        out["feedback"] = None
    return out
