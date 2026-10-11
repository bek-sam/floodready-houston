"""Answer cache for location-independent questions (memory + SQLite, TTL 6 h), with a semantic match
(Gemini embeddings, cosine >= 0.92). Never used for location-dependent, personal, follow-up or emergency questions.
Also: optional Gemini explicit context cache for the static system prompt + knowledge digest."""
import json
import os
import re
import sqlite3
import sys
import threading
import time
import unicodedata

import numpy as np

from .config import BACKEND

TTL_S = 6 * 3600
SIM = 0.92
# Intents whose answers come from the static knowledge base only (no location tools).
KNOWLEDGE_INTENTS = {"insurance", "recovery", "civic", "general"}
# Personal / location / time-sensitive cues -> not cacheable (en, es, vi, zh, ar).
PERSONAL = re.compile(
    r"\b(my|me|mine|our|we|us|here|near|nearby|around|address|street|neighbou?rhood|zip|today|tonight|now|right now|current\w*|"
    r"mi|mis|nuestr\w+|aqu[ií]|cerca|direcci[oó]n|calle|barrio|hoy|ahora)\b|"
    r"của tôi|nhà tôi|ở đây|gần|hiện giờ|bây giờ|我的|我家|这里|附近|现在|今天|عنواني|منزلي|بيتي|هنا|قريب|الآن|اليوم|\d{5}", re.I)
_lock = threading.Lock()
_mem: dict[str, dict] = {}


def enabled() -> bool:
    return os.getenv("AI_CACHE", "0" if "pytest" in sys.modules else "1") != "0"


def db_path() -> str:
    return os.getenv("AI_CACHE_DB") or str(BACKEND / ".cache" / "ai_answer_cache.sqlite")


def normalize(q: str) -> str:
    t = unicodedata.normalize("NFKC", q or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def key(question: str, lang: str, mode: str | None) -> str:
    return f"{'voice' if mode == 'voice' else 'chat'}2|{lang or 'en'}|{normalize(question)}"


def cacheable(s: dict) -> bool:
    """Only knowledge questions: no history, no danger/location intents, no personal/time cues."""
    if not enabled() or s.get("history"):
        return False
    intents = set(s.get("intents") or [])
    if not intents or not intents <= KNOWLEDGE_INTENTS:
        return False
    return not PERSONAL.search(s.get("question", ""))


# ---------- storage ----------
def _conn():
    p = db_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c = sqlite3.connect(p, timeout=2)
    c.execute("CREATE TABLE IF NOT EXISTS answers (k TEXT PRIMARY KEY, prefix TEXT, created REAL, emb TEXT, payload TEXT)")
    return c


def _prefix(k: str) -> str:
    return k.split("|", 2)[0] + "|" + k.split("|", 2)[1]


def _load_prefix(prefix: str) -> list[dict]:
    """Fresh entries for one mode+lang (memory first, then SQLite)."""
    now = time.time()
    with _lock:
        rows = [v for k, v in _mem.items() if k.startswith(prefix + "|") and now - v["created"] < TTL_S]
    if rows:
        return rows
    try:
        with _conn() as c:
            db = c.execute("SELECT k, created, emb, payload FROM answers WHERE prefix=? AND created>?", (prefix, now - TTL_S)).fetchall()
    except Exception:  # noqa: BLE001
        return []
    out = []
    with _lock:
        for k, created, emb, payload in db:
            e = {"k": k, "created": created, "emb": json.loads(emb) if emb else None, "payload": json.loads(payload)}
            _mem[k] = e
            out.append(e)
    return out


def get_exact(k: str) -> dict | None:
    now = time.time()
    with _lock:
        e = _mem.get(k)
    if e is None:
        try:
            with _conn() as c:
                r = c.execute("SELECT created, emb, payload FROM answers WHERE k=?", (k,)).fetchone()
        except Exception:  # noqa: BLE001
            r = None
        if r:
            e = {"k": k, "created": r[0], "emb": json.loads(r[1]) if r[1] else None, "payload": json.loads(r[2])}
            with _lock:
                _mem[k] = e
    if e and now - e["created"] < TTL_S:
        return e["payload"]
    return None


def get_semantic(k: str, emb) -> tuple[dict, float] | None:
    if emb is None:
        return None
    q = np.asarray(emb, dtype=np.float32)
    best, score = None, -1.0
    for e in _load_prefix(_prefix(k)):
        if e.get("emb") is None:
            continue
        v = np.asarray(e["emb"], dtype=np.float32)
        s = float(q @ v / max(np.linalg.norm(q) * np.linalg.norm(v), 1e-9))
        if s > score:
            best, score = e, s
    return (best["payload"], score) if best is not None and score >= SIM else None


def put(k: str, payload: dict, emb=None) -> None:
    e = {"k": k, "created": time.time(), "emb": list(map(float, emb)) if emb is not None else None, "payload": payload}
    with _lock:
        _mem[k] = e
    try:
        with _conn() as c:
            c.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?,?,?)",
                      (k, _prefix(k), e["created"], json.dumps(e["emb"]) if e["emb"] else None, json.dumps(payload, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        pass


def clear() -> None:
    with _lock:
        _mem.clear()
    try:
        with _conn() as c:
            c.execute("DELETE FROM answers")
    except Exception:  # noqa: BLE001
        pass


# ---------- Gemini explicit context cache (static system prompt + knowledge digest) ----------
_ctx: dict[str, tuple[str, float]] = {}  # (model, kind) -> (cache name, expires_at)
_ctx_off_until = 0.0
_ctx_lock = threading.Lock()
CTX_TTL_S = 6 * 3600


def ctx_enabled() -> bool:
    return os.getenv("AI_CONTEXT_CACHE", "1") != "0" and time.time() >= _ctx_off_until


def digest() -> str:
    """Compact digest of every knowledge card chunk with its source URL."""
    from . import rag
    ch = [c for c in rag.get_index().chunks if c["file"] not in ("flood-problems.md", "research-brief.md")]
    return "Knowledge digest (sourced):\n" + "\n".join(f"- {c['title']}: {c['text']} <{c['source']}>" for c in ch)


def ctx_name(model: str, kind: str) -> str | None:
    """Existing live cache name for (model, kind), or None. Never blocks on creation."""
    if not ctx_enabled():
        return None
    v = _ctx.get(f"{model}|{kind}")
    return v[0] if v and v[1] > time.time() + 60 else None


def ctx_create(client, types, model: str, kind: str, system: str) -> str | None:
    """Create the cache (call from a background thread). On any failure (e.g. free tier: storage limit 0)
    caching is switched off for an hour."""
    global _ctx_off_until
    if not ctx_enabled():
        return None
    with _ctx_lock:
        if ctx_name(model, kind):
            return ctx_name(model, kind)
        try:
            cc = client.caches.create(model=model, config=types.CreateCachedContentConfig(
                system_instruction=system, display_name=f"floodready-{kind}",
                contents=[types.Content(role="user", parts=[types.Part(text=digest())])], ttl=f"{CTX_TTL_S}s"))
            _ctx[f"{model}|{kind}"] = (cc.name, time.time() + CTX_TTL_S)
            return cc.name
        except Exception:  # noqa: BLE001
            _ctx_off_until = time.time() + 3600
            return None


def ctx_drop(model: str, kind: str) -> None:
    _ctx.pop(f"{model}|{kind}", None)
