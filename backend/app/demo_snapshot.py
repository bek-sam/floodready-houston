"""Demo snapshot mode: serve pre-recorded API responses when the venue network fails.

Only installed when DEMO_SNAPSHOT=1 (see install()): the snapshot then wins for any recorded request; other
requests go to the live handlers. Without the flag the middleware is not installed at all, so production never
answers from recorded data. Snapshots live in data/demo_snapshot/*.json
(written by scripts/record_demo.py). Writes (/reports, /watch, /push, /feedback) and voice/live are never served
from a snapshot. Never raises: any problem falls through to the normal response."""
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import DATA_DIR

log = logging.getLogger("demo_snapshot")
SNAP_DIR = Path(DATA_DIR) / "demo_snapshot"
NEVER = ("/api/reports", "/api/watch", "/api/push", "/api/feedback", "/api/voice", "/api/live", "/api/demo")
HEADER = "X-FloodReady-Snapshot"
_index: dict[str, dict] | None = None


def _norm_q(s: str) -> str:
    return " ".join((s or "").lower().split())


def make_key(method: str, path: str, query: str = "", body: bytes | None = None) -> str:
    """method + path + sorted query (+ canonical body for POST). /ask keys on question+lang only."""
    method = method.upper()
    key = f"{method} {path}"
    items = sorted(parse_qsl(query or "", keep_blank_values=True))
    if items:
        key += "?" + "&".join(f"{k}={v}" for k, v in items)
    if method == "POST" and body:
        try:
            b = json.loads(body)
        except Exception:  # noqa: BLE001
            b = None
        if isinstance(b, dict) and path.rstrip("/") == "/api/ask":
            key += "#" + _norm_q(str(b.get("question", ""))) + "|" + str(b.get("lang", "en"))
        elif isinstance(b, dict) and path.rstrip("/") == "/api/route-check":
            def pt(p):
                p = p or {}
                return f"{float(p.get('lat', 0)):.4f},{float(p.get('lon', 0)):.4f}"
            key += "#" + pt(b.get("origin")) + ">" + pt(b.get("destination"))
        elif b is not None:
            key += "#" + hashlib.sha1(json.dumps(b, sort_keys=True).encode()).hexdigest()[:10]
    return key


def file_name(key: str) -> str:
    slug = "".join(ch if ch.isalnum() else "_" for ch in key.split("#")[0].split("?")[0])[:60].strip("_")
    return f"{slug}-{hashlib.sha1(key.encode()).hexdigest()[:8]}.json"


def load(force: bool = False) -> dict[str, dict]:
    global _index
    if _index is None or force:
        _index = {}
        for f in sorted(SNAP_DIR.glob("*.json")):
            try:
                d = json.loads(f.read_text())
                if isinstance(d, dict) and d.get("key"):
                    _index[d["key"]] = d
            except Exception as e:  # noqa: BLE001
                log.warning("bad snapshot %s: %s", f.name, e)
    return _index


def _serve(entry: dict) -> Response:
    body = entry.get("body")
    date = entry.get("recorded_at", "")
    if isinstance(body, dict):
        m = dict(body.get("meta") or {})
        m.update({"freshness": "snapshot", "snapshot_date": date})
        m.setdefault("as_of", date)
        m.setdefault("source", "demo_snapshot")
        body = {**body, "meta": m}
    return Response(json.dumps(body), status_code=int(entry.get("status", 200)), media_type="application/json",
                    headers={HEADER: "1", "X-FloodReady-Snapshot-Date": date,
                             "Access-Control-Expose-Headers": f"{HEADER}, X-FloodReady-Snapshot-Date"})


class SnapshotMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path.startswith(NEVER):
            return await call_next(request)
        entry = None
        try:
            raw = await request.body() if request.method == "POST" else None
            entry = load().get(make_key(request.method, path, request.url.query, raw))
        except Exception as e:  # noqa: BLE001
            log.warning("snapshot lookup failed: %s", e)
        if entry:
            return _serve(entry)
        return await call_next(request)


def find_voice(lang: str = "es") -> Path | None:
    """Existing cached mp3 for the canned pitch answer in `lang` (never generates audio)."""
    if lang not in ("en", "es", "vi", "zh", "ar"):
        return None
    pre = Path(__file__).resolve().parents[2] / "data" / "demo_snapshot" / f"voice-{lang}.mp3"
    if pre.exists():
        return pre
    from app.ai.voice import CACHE
    voice = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
    for entry in load().values():
        if entry.get("path") != "/api/ask" or entry.get("lang") != lang or not isinstance(entry.get("body"), dict):
            continue
        b = entry["body"]
        for text in (b.get("speak"), b.get("answer")):
            if not text:
                continue
            for model in ("eleven_flash_v2_5", os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")):
                h = hashlib.sha256(f"{str(text)[:2500]}|{lang}|{voice}|{model}".encode()).hexdigest()[:24]
                if (CACHE / f"{h}.mp3").exists():
                    return CACHE / f"{h}.mp3"
    return None


def enabled() -> bool:
    return os.getenv("DEMO_SNAPSHOT") == "1"


def install(app) -> None:
    if enabled():
        app.add_middleware(SnapshotMiddleware)

    @app.get("/api/demo/voice")
    async def demo_voice(lang: str = "es"):
        p = find_voice(lang)
        if not p:
            return Response(status_code=404)
        return Response(p.read_bytes(), media_type="audio/mpeg")
