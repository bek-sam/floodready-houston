"""WebSocket /live: bridge browser <-> Gemini Live (engine B, Voice v2).

Server -> client JSON: ready, turn(user_end|model_start|model_end, t=epoch ms), caption(role,text,final,delta),
transcript (legacy), thinking(label|null), tool (legacy), resume(handle), interrupted, error. Binary = PCM16 24 kHz.
Client -> server: binary PCM16 16 kHz; JSON end | text | ptt{down} | mute{on}.
"""
import asyncio
import contextlib
import json
import logging
import time
from array import array
from typing import Optional

from fastapi import APIRouter, WebSocket
from google.genai import types

from app.ai import live

log = logging.getLogger("floodready.live")
router = APIRouter()
_active = 0
VOICE_RMS = 490  # PCM16 RMS (~0.015 full scale) that counts as user speech for turn timing
PTT_BUFFER_MAX = 16000 * 2 * 5  # 5 s of 16 kHz PCM16 kept while switching to push-to-talk


def now_ms() -> int:
    return int(time.time() * 1000)


async def _send_json(ws: WebSocket, obj: dict):
    with contextlib.suppress(Exception):
        await ws.send_text(json.dumps(obj, ensure_ascii=False))


class Bridge:
    def __init__(self, ws: WebSocket, client, lang: str, lat, lon, context: str, manual: bool, resume: Optional[str]):
        self.ws, self.client, self.lang, self.lat, self.lon = ws, client, lang, lat, lon
        self.context, self.manual, self.handle = context, manual, resume
        self.session = None
        self.model = ""
        self.stack: Optional[contextlib.AsyncExitStack] = None
        self.down_task: Optional[asyncio.Task] = None
        self.ended = asyncio.Event()  # set when the Gemini side ends for good
        self.swapping = False
        self.swap_lock = asyncio.Lock()
        self.auto_after_ptt = False  # session started hands-free: return to it once the push-to-talk turn is answered
        self.ptt_active = False
        self.muted = False
        self.pending_audio: list[bytes] = []
        self.tool_tasks: dict[str, asyncio.Task] = {}
        self.error_sent = False
        self.last_voice_ms: Optional[int] = None
        self._reset_turn()

    def _reset_turn(self):
        self.user_ended = False
        self.model_started = False
        self.tool_called = False
        self.cap = {"user": "", "model": ""}

    @property
    def non_blocking(self) -> bool:
        return live.features(self.model or live.DEFAULT_MODEL)["non_blocking"]

    async def send(self, obj: dict):
        await _send_json(self.ws, obj)

    async def error(self, detail: str):
        self.error_sent = True
        await self.send({"type": "error", "detail": detail})

    # ---- session lifecycle ----
    async def connect(self, models: Optional[list[str]] = None):
        stack = contextlib.AsyncExitStack()
        try:
            sess, model = await live.connect_with_fallback(
                stack, self.client, self.lang, self.lat, self.lon, context=self.context, manual=self.manual,
                resume_handle=self.handle, models=models)
        except BaseException:
            with contextlib.suppress(BaseException):
                await stack.aclose()
            raise
        self.session, self.model, self.stack = sess, model, stack
        self.down_task = asyncio.create_task(self._down(sess))

    async def close_session(self):
        t, self.down_task = self.down_task, None
        if t and t is not asyncio.current_task():
            t.cancel()
            with contextlib.suppress(BaseException):
                await t
        for task in list(self.tool_tasks.values()):
            task.cancel()
        self.tool_tasks.clear()
        st, self.stack = self.stack, None
        self.session = None
        if st:
            with contextlib.suppress(BaseException):
                await st.aclose()

    async def reconnect(self, manual: Optional[bool] = None):
        """Swap the Gemini session (resume handle keeps the conversation): PTT mode switch or go_away."""
        async with self.swap_lock:
            await self._swap(manual)

    async def _swap(self, manual: Optional[bool] = None):
        self.swapping = True
        try:
            if manual is not None:
                self.manual = manual
            model = self.model
            await self.close_session()
            try:
                await self.connect([model] if model else None)
            except Exception:  # noqa: BLE001  handle rejected -> fresh session on the same model chain
                self.handle = None
                await self.connect()
        finally:
            self.swapping = False

    async def _to_auto(self):
        try:
            async with self.swap_lock:
                if self.manual and not self.ptt_active:
                    await self._swap(False)
                    await self._flush_pending()
        except Exception as e:  # noqa: BLE001
            log.warning("live return to hands-free failed: %s", e)
            await self.error("session ending")
            self.ended.set()

    # ---- browser -> Gemini ----
    async def _audio(self, data: bytes):
        if self.muted:
            return
        if self.manual and not self.ptt_active:
            return  # push-to-talk: only stream while the button is held
        if len(data) >= 64:  # last loud mic frame = real end of user speech (Gemini only reports it with the answer)
            smp = array("h", data[: len(data) // 2 * 2])[::4]
            if smp and (sum(x * x for x in smp) / len(smp)) ** 0.5 > VOICE_RMS:
                self.last_voice_ms = now_ms()
        if self.swapping or self.session is None:
            if sum(map(len, self.pending_audio)) < PTT_BUFFER_MAX:
                self.pending_audio.append(data)
            return
        await self.session.send_realtime_input(audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000"))

    async def _flush_pending(self):
        buf, self.pending_audio = self.pending_audio, []
        for b in buf:
            await self._audio(b)

    async def up(self):
        while True:
            msg = await self.ws.receive()
            if msg.get("type") == "websocket.disconnect":
                return
            if msg.get("bytes"):
                await self._audio(msg["bytes"])
                continue
            if not msg.get("text"):
                continue
            try:
                data = json.loads(msg["text"])
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            t = data.get("type")
            if t == "end":
                with contextlib.suppress(Exception):
                    await self.session.send_realtime_input(audio_stream_end=True)
                return
            if t == "text" and str(data.get("text", "")).strip():
                self._reset_turn()
                self.user_ended = True
                await self.send({"type": "turn", "event": "user_end", "t": now_ms()})
                await self.session.send_realtime_input(text=str(data["text"])[:2000])
            elif t == "ptt":
                await self._ptt(bool(data.get("down")))
            elif t == "mute":
                self.muted = bool(data.get("on"))
                if self.muted and not self.manual and self.session is not None:
                    with contextlib.suppress(Exception):  # flush VAD so a half-spoken turn still completes
                        await self.session.send_realtime_input(audio_stream_end=True)

    async def _ptt(self, down: bool):
        if down:
            if self.ptt_active:
                return
            self.ptt_active = True
            if not self.manual:
                self.auto_after_ptt = True
                await self.reconnect(manual=True)
            await self.session.send_realtime_input(activity_start=types.ActivityStart())
            self._reset_turn()
            await self._flush_pending()
        else:
            if not self.ptt_active:
                return
            await self._flush_pending()
            self.ptt_active = False
            if self.session is not None:
                await self.session.send_realtime_input(activity_end=types.ActivityEnd())
            await self._user_end(now_ms())

    # ---- Gemini -> browser ----
    async def _user_end(self, at: Optional[int] = None):
        if not self.user_ended:
            self.user_ended = True
            t, lv = now_ms(), self.last_voice_ms
            self.last_voice_ms = None
            await self.send({"type": "turn", "event": "user_end", "t": at or (lv if lv and lv <= t else t)})

    async def _caption(self, role: str, tr):
        text = getattr(tr, "text", None) or ""
        finished = bool(getattr(tr, "finished", False))
        if not text and not finished:
            return
        if text:
            self.cap[role] += text
            await self.send({"type": "transcript", "role": role, "text": text})  # legacy v1 event
        await self.send({"type": "caption", "role": role, "text": self.cap[role], "delta": text, "final": finished})
        if finished:
            self.cap[role] = ""

    async def _final_captions(self):
        for role in ("user", "model"):
            if self.cap[role]:
                await self.send({"type": "caption", "role": role, "text": self.cap[role], "delta": "", "final": True})
                self.cap[role] = ""

    async def _run_tool(self, session, fc):
        label = live.TOOL_LABELS.get(fc.name, "Checking")
        await self.send({"type": "tool", "name": fc.name})
        await self.send({"type": "thinking", "label": label})
        try:
            out = await live.execute_tool(fc.name, dict(fc.args or {}))
            await session.send_tool_response(
                function_responses=[live.function_response(fc.id, fc.name, out, self.non_blocking)])
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            log.warning("live tool %s failed: %s", fc.name, e)
        finally:
            self.tool_tasks.pop(str(fc.id), None)
            if not self.tool_tasks:
                await self.send({"type": "thinking", "label": None})

    async def _handle(self, session, m):
        sru = getattr(m, "session_resumption_update", None)
        if sru and getattr(sru, "new_handle", None) and getattr(sru, "resumable", True) is not False:
            self.handle = sru.new_handle
            await self.send({"type": "resume", "handle": sru.new_handle})
        va = getattr(m, "voice_activity", None)
        if va is not None:
            vt = str(getattr(va, "voice_activity_type", "") or "")
            if vt.endswith("ACTIVITY_START"):
                self._reset_turn()
            elif vt.endswith("ACTIVITY_END"):
                await self._user_end()
        sc = m.server_content
        if sc:
            if sc.interrupted:
                await self.send({"type": "interrupted"})
                await self._final_captions()
                self._reset_turn()
            if sc.input_transcription:
                await self._caption("user", sc.input_transcription)
            if sc.model_turn or sc.output_transcription:
                await self._user_end()
            if sc.output_transcription:
                await self._caption("model", sc.output_transcription)
            if sc.model_turn:
                for p in sc.model_turn.parts or []:
                    if p.inline_data and p.inline_data.data:
                        if not self.model_started:
                            self.model_started = True
                            await self.send({"type": "turn", "event": "model_start", "t": now_ms()})
                        await self.ws.send_bytes(p.inline_data.data)
            if sc.turn_complete:
                await self._user_end()
                await self._final_captions()
                # NON_BLOCKING tools: the model may close a silent turn right after calling a tool and speak the
                # result in the next one -> keep the logical turn open until audio has been produced.
                if self.model_started or not (self.tool_called or self.tool_tasks):
                    await self.send({"type": "turn", "event": "model_end", "t": now_ms()})
                    self._reset_turn()
                    if self.auto_after_ptt and self.manual and not self.ptt_active:
                        self.auto_after_ptt = False
                        return "auto"
        if m.tool_call and m.tool_call.function_calls:
            await self._user_end()
            self.tool_called = True
            for fc in m.tool_call.function_calls:
                self.tool_tasks[str(fc.id)] = asyncio.create_task(self._run_tool(session, fc))
        tcc = getattr(m, "tool_call_cancellation", None)
        if tcc and getattr(tcc, "ids", None):
            for i in tcc.ids:
                task = self.tool_tasks.pop(str(i), None)
                if task:
                    task.cancel()
            if not self.tool_tasks:
                await self.send({"type": "thinking", "label": None})
        if m.go_away:
            return "go_away"
        return None

    async def _down(self, session):
        """Gemini -> browser for one session. receive() ends per turn, so loop."""
        try:
            while True:
                async for m in session.receive():
                    r = await self._handle(session, m)
                    if r == "auto":
                        asyncio.create_task(self._to_auto())
                        return
                    if r == "go_away":
                        if self.handle:
                            asyncio.create_task(self._go_away())
                        else:
                            await self.error("session ending")
                            self.ended.set()
                        return
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            if self.swapping:
                return
            log.warning("live bridge error: %s", e)
            await self.error("Live session ended unexpectedly.")
            self.ended.set()

    async def _go_away(self):
        try:
            await self.reconnect()
        except Exception as e:  # noqa: BLE001
            log.warning("live resume failed: %s", e)
            await self.error("session ending")
            self.ended.set()


async def _connect_first(br: Bridge, resume: Optional[str]) -> bool:
    for attempt in range(2 if resume else 1):
        try:
            await br.connect()
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("live connect failed: %s", e)
            br.handle = None  # stale resume handle -> fresh session
    return False


@router.websocket("/live")
async def live_ws(ws: WebSocket, lang: str = "en", lat: Optional[float] = None, lon: Optional[float] = None,
                  place: Optional[str] = None, profile: Optional[str] = None, resume: Optional[str] = None,
                  ptt: bool = False):
    global _active
    await ws.accept()
    client = live.make_client()
    if client is None:
        await _send_json(ws, {"type": "error", "detail": "Gemini Live is not configured (no API key)."})
        with contextlib.suppress(Exception):
            await ws.close(code=1011)
        return
    if _active >= live.MAX_CONNECTIONS:
        await _send_json(ws, {"type": "error", "detail": "Too many live sessions, try again shortly."})
        with contextlib.suppress(Exception):
            await ws.close(code=1013)
        return
    _active += 1
    br: Optional[Bridge] = None
    try:
        t0 = time.monotonic()
        context = await live.build_context(lat, lon, place, live.decode_profile(profile))
        br = Bridge(ws, client, lang, lat, lon, context, manual=ptt, resume=resume)
        if not await _connect_first(br, resume):
            await _send_json(ws, {"type": "error", "detail": "Could not start the live voice session."})
            return
        await br.send({"type": "ready", "model": br.model, "latency_hint": live.LATENCY_HINT_MS.get(br.model),
                       "mode": "ptt" if br.manual else "auto", "setup_ms": int((time.monotonic() - t0) * 1000)})
        up = asyncio.create_task(br.up())
        ended = asyncio.create_task(br.ended.wait())
        done, pending = await asyncio.wait({up, ended}, timeout=live.max_session_seconds(),
                                           return_when=asyncio.FIRST_COMPLETED)
        if not done:
            await br.error("Session time limit reached.")
        for t in pending:
            t.cancel()
        for t in (up, ended):
            with contextlib.suppress(BaseException):
                await t
        if up in done and not up.cancelled() and up.exception() and not br.error_sent:
            exc = up.exception()
            if type(exc).__name__ not in {"WebSocketDisconnect", "ClientDisconnected"}:
                log.warning("live bridge error: %s", exc)
                await br.error("Live session ended unexpectedly.")
    except Exception as e:  # noqa: BLE001
        log.warning("live session error: %s", e)
    finally:
        _active -= 1
        if br is not None:
            with contextlib.suppress(BaseException):
                await br.close_session()
        with contextlib.suppress(Exception):
            await ws.close()
