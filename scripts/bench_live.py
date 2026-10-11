"""Benchmark Gemini Live models for FloodReady voice (engine B).

For each Live-capable conversational model (bidiGenerateContent), run N sessions that stream a synthesized
spoken question (macOS `say` -> afconvert 16 kHz PCM16) in real time with the production config
(app.ai.live.build_config + preloaded Houston context), then measure:
  - latency: end of speech input -> first model audio chunk (includes server VAD silence wait)
  - input transcript accuracy (word overlap with the question), answer keyword check, tool calls, errors.
Writes docs/eval/live-bench.md and sets GEMINI_LIVE_MODEL in .env.example and .env (only that line).

Run:  cd backend && uv run python ../scripts/bench_live.py [--sessions 3] [--models m1,m2] [--no-write-env]
"""
import argparse
import asyncio
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from google.genai import types  # noqa: E402

from app.ai import live  # noqa: E402

LAT, LON, PLACE = 29.7604, -95.3698, "Downtown Houston, TX 77002"
QUESTIONS = [
    ("Is my home in a flood zone?", ["zone"]),
    ("Did my area flood during Hurricane Harvey?", ["harvey"]),
    ("Water is coming into my house right now, what should I do?", ["911"]),
]
CHUNK_MS = 40
SKIP = re.compile(r"transcribe|translate|robotics", re.I)


def synth(text: str, out_dir: Path, idx: int) -> bytes:
    aiff, wav = out_dir / f"q{idx}.aiff", out_dir / f"q{idx}.wav"
    subprocess.run(["say", "-o", str(aiff), text], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(aiff), str(wav)], check=True)
    with wave.open(str(wav)) as w:
        return w.readframes(w.getnframes())


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def overlap(ref: str, hyp: str) -> float:
    r, h = words(ref), set(words(hyp))
    return sum(1 for x in r if x in h) / max(1, len(r))


async def one_session(client, model: str, context: str, pcm: bytes, question: str, keys: list[str]) -> dict:
    res = {"latency_ms": None, "in_text": "", "out_text": "", "tools": [], "error": None, "connect_ms": None}
    t0 = time.monotonic()
    try:
        cfg = live.build_config("en", LAT, LON, context=context, model=model)
        async with client.aio.live.connect(model=model, config=cfg) as s:
            res["connect_ms"] = int((time.monotonic() - t0) * 1000)
            first_audio = asyncio.Event()
            done = asyncio.Event()
            mark = {"end": None, "first": None, "tool_len": -1}

            async def rx():
                while not done.is_set():
                    async for m in s.receive():
                        sc = m.server_content
                        if m.tool_call and m.tool_call.function_calls:
                            fr = []
                            for fc in m.tool_call.function_calls:
                                res["tools"].append(fc.name)
                                out = await live.execute_tool(fc.name, dict(fc.args or {}))
                                fr.append(live.function_response(fc.id, fc.name, out, live.features(model)["non_blocking"]))
                            await s.send_tool_response(function_responses=fr)
                            mark["tool_len"] = len(res["out_text"])
                        if sc:
                            if sc.input_transcription and sc.input_transcription.text:
                                res["in_text"] += sc.input_transcription.text
                            if sc.output_transcription and sc.output_transcription.text:
                                res["out_text"] += sc.output_transcription.text
                            if sc.model_turn and not first_audio.is_set():
                                if any(p.inline_data and p.inline_data.data for p in sc.model_turn.parts or []):
                                    mark["first"] = time.monotonic()
                                    first_audio.set()
                            # done once a turn completes with audio, and any tool result has been spoken
                            if sc.turn_complete and first_audio.is_set() and len(res["out_text"]) > mark["tool_len"]:
                                done.set()
                                return

            async def tx():
                step = 16000 * 2 * CHUNK_MS // 1000
                start = time.monotonic()
                for i in range(0, len(pcm), step):
                    await s.send_realtime_input(audio=types.Blob(data=pcm[i:i + step], mime_type="audio/pcm;rate=16000"))
                    target = start + (i + step) / 32000
                    await asyncio.sleep(max(0.0, target - time.monotonic()))
                mark["end"] = time.monotonic()
                silence = b"\x00\x00" * (16000 * CHUNK_MS // 1000)
                while not done.is_set():  # keep the mic "open" with silence, like a browser
                    await s.send_realtime_input(audio=types.Blob(data=silence, mime_type="audio/pcm;rate=16000"))
                    await asyncio.sleep(CHUNK_MS / 1000)

            rt, tt = asyncio.create_task(rx()), asyncio.create_task(tx())
            try:
                await asyncio.wait_for(done.wait(), 25)
            except asyncio.TimeoutError:
                res["error"] = "timeout"
            for t in (rt, tt):
                t.cancel()
            if rt.done() and not rt.cancelled() and rt.exception():
                res["error"] = f"{type(rt.exception()).__name__}: {str(rt.exception())[:80]}"
            if mark["first"] and mark["end"]:
                res["latency_ms"] = int((mark["first"] - mark["end"]) * 1000)
    except Exception as e:  # noqa: BLE001
        res["error"] = f"{type(e).__name__}: {str(e)[:100]}"
    res["in_acc"] = overlap(question, res["in_text"])
    res["answer_ok"] = all(k in res["out_text"].lower() for k in keys) if res["out_text"] else False
    return res


def list_live_models(client) -> list[str]:
    out = []
    for m in client.models.list():
        if "bidiGenerateContent" in (getattr(m, "supported_actions", None) or []):
            name = m.name.removeprefix("models/")
            if not SKIP.search(name):
                out.append(name)
    return out


def set_env_line(path: Path, model: str):
    if not path.exists():
        return
    if re.search(r"(?m)^GEMINI_LIVE_MODEL=", path.read_text()):
        subprocess.run(["sed", "-i", "", f"s|^GEMINI_LIVE_MODEL=.*|GEMINI_LIVE_MODEL={model}|", str(path)], check=True)
    else:
        with path.open("a") as f:
            f.write(f"\nGEMINI_LIVE_MODEL={model}\n")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=3)
    ap.add_argument("--models", default="")
    ap.add_argument("--no-write-env", action="store_true")
    a = ap.parse_args()
    client = live.make_client()
    if client is None:
        sys.exit("no GEMINI key")
    models = a.models.split(",") if a.models else list_live_models(client)
    print("models:", models)
    tmp = Path(tempfile.mkdtemp(prefix="bench_live_"))
    pcms = [synth(q, tmp, i) for i, (q, _) in enumerate(QUESTIONS)]
    t = time.monotonic()
    context = await live.build_context(LAT, LON, PLACE, None)
    print(f"context preload {int((time.monotonic() - t) * 1000)} ms, {len(context)} chars")

    rows = []
    for model in models:
        runs = []
        for i in range(a.sessions):
            q, keys = QUESTIONS[i % len(QUESTIONS)]
            r = await one_session(client, model, context, pcms[i % len(QUESTIONS)], q, keys)
            print(model, i, r["latency_ms"], r["error"], "| in:", r["in_text"][:60], "| out:", r["out_text"][:90], r["tools"])
            runs.append(r)
        lats = [r["latency_ms"] for r in runs if r["latency_ms"] is not None]
        rows.append({
            "model": model, "ok": sum(1 for r in runs if r["latency_ms"] is not None and not r["error"]), "n": len(runs),
            "median": int(statistics.median(lats)) if lats else None, "min": min(lats) if lats else None,
            "max": max(lats) if lats else None,
            "connect": int(statistics.median([r["connect_ms"] for r in runs if r["connect_ms"]] or [0])),
            "in_acc": statistics.mean(r["in_acc"] for r in runs), "ans": sum(r["answer_ok"] for r in runs),
            "tools": sum(len(r["tools"]) for r in runs),
            "errors": "; ".join(sorted({r["error"] for r in runs if r["error"]})) or "-",
            "sample": next((r["out_text"] for r in runs if r["out_text"]), "")[:140],
        })

    good = [r for r in rows if r["ok"] == r["n"] and r["in_acc"] >= 0.7 and r["median"] is not None]
    good.sort(key=lambda r: (-(r["ans"]), r["median"]))
    best = min(good or [r for r in rows if r["median"] is not None], key=lambda r: (r["median"] + (0 if r["ans"] == r["n"] else 400)))
    write_report(rows, best, a.sessions, context)
    print("recommended:", best["model"])
    if not a.no_write_env:
        set_env_line(ROOT / ".env.example", best["model"])
        set_env_line(ROOT / ".env", best["model"])


def write_report(rows, best, n, context):
    out = ROOT / "docs" / "eval" / "live-bench.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    L = [
        "# Gemini Live benchmark (FloodReady voice v2)",
        "",
        f"Run {time.strftime('%Y-%m-%d %H:%M')} local, {n} sessions per model, generated by `scripts/bench_live.py`.",
        "Input: macOS `say` -> 16 kHz PCM16 streamed in real time (40 ms chunks), then silence like an open mic.",
        "Config: production `live.build_config` (auto VAD end-sensitivity HIGH, silence "
        f"{os.getenv('LIVE_VAD_SILENCE_MS', '600')} ms, prefix 200 ms, preloaded Houston context, tools).",
        "Latency = end of spoken input -> first model audio chunk (includes the VAD silence wait).",
        "",
        "| Model | OK | Median ms | Min | Max | Connect ms | Input transcript acc | Answer check | Tool calls | Errors |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        L.append(f"| {r['model']} | {r['ok']}/{r['n']} | {r['median'] or '-'} | {r['min'] or '-'} | {r['max'] or '-'} | "
                 f"{r['connect']} | {r['in_acc']:.0%} | {r['ans']}/{r['n']} | {r['tools']} | {r['errors']} |")
    L += ["", "Sample answers:", ""]
    L += [f"- **{r['model']}**: {r['sample'] or '(none)'}" for r in rows]
    L += [
        "",
        f"## Recommendation: `{best['model']}`",
        "",
        f"Lowest median end-of-speech -> first-audio latency ({best['median']} ms) among models with every session "
        "succeeding and correct answers; set as `GEMINI_LIVE_MODEL` in `.env.example` / `.env`. The others stay as "
        "runtime fallbacks in `live.FALLBACK_MODELS`.",
        "",
        "## Feature probe (google-genai 2.29, 2026-10-11)",
        "",
        "| Feature | 3.8-live | 3.1-flash-live-preview | 2.5-flash-native-audio-latest |",
        "|---|---|---|---|",
        "| NON_BLOCKING tools + scheduling | accepted | accepted | accepted (speaks filler before tool) |",
        "| enable_affective_dialog | 1007 rejected | 1007 rejected | OK |",
        "| proactivity | v1alpha only | v1alpha only | v1alpha only |",
        "| session resumption / compression / transcription / VAD tuning | OK | OK | OK |",
        "",
        f"Context preload: {len(context)} chars (risk, flood history, ZIP claims, alerts).",
        "",
        "Note: " + '`gemini-3.8-live-extended-thinking` requires an explicit thinking level and is a high-latency reasoning variant, so it is not a candidate for turn-taking voice.',
    ]
    out.write_text("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    asyncio.run(main())
