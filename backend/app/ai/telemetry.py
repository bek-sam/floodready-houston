"""Per-request AI telemetry: route, model, tokens, ESTIMATED cost, stage latencies, cache hit.
Records go to an in-memory ring + a JSONL file; GET /ai/stats aggregates the last N.
Also stores answer feedback (POST /feedback) in the app DB."""
import contextlib
import contextvars
import json
import os
import statistics
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone

from . import trace as _tr
from .config import BACKEND, sqlalchemy_url

# USD per 1M tokens. ESTIMATES ONLY (list prices as we understood them; check ai.google.dev/pricing).
# Models not in the table use DEFAULT_PRICE. cached = price for context-cached input tokens.
PRICE_TABLE_IS_ESTIMATE = True
PRICES = {
    "gemini-2.5-flash": {"in": 0.30, "out": 2.50, "cached": 0.03},
    "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40, "cached": 0.01},
    "gemini-3.5-flash-lite": {"in": 0.10, "out": 0.40, "cached": 0.01},
    "gemini-3.5-flash": {"in": 0.30, "out": 2.50, "cached": 0.03},
    "gemini-embedding-001": {"in": 0.15, "out": 0.0, "cached": 0.0},
}
DEFAULT_PRICE = {"in": 0.30, "out": 2.50, "cached": 0.03}

_current: contextvars.ContextVar["Trace | None"] = contextvars.ContextVar("ai_trace", default=None)
_ring: deque = deque(maxlen=1000)
_lock = threading.Lock()


def _testing() -> bool:
    return "pytest" in sys.modules


def log_path():
    return os.getenv("AI_TELEMETRY_LOG") or str(BACKEND / ".cache" / "ai_telemetry.jsonl")


def est_cost(model: str, prompt: int, completion: int, cached: int = 0) -> float:
    p = PRICES.get(model or "", DEFAULT_PRICE)
    fresh = max(prompt - cached, 0)
    return (fresh * p["in"] + cached * p["cached"] + completion * p["out"]) / 1e6


class Trace:
    def __init__(self, endpoint: str, question: str = "", lang: str = "en"):
        self.t0 = time.perf_counter()
        self.rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "endpoint": endpoint,
                    "lang": lang, "qlen": len(question or ""), "route": "", "intents": [], "models": [],
                    "llm_calls": 0, "embed_calls": 0, "prompt_tokens": 0, "completion_tokens": 0,
                    "cached_tokens": 0, "est_cost_usd": 0.0, "stages_ms": {}, "cache_hit": "none",
                    "grounding_removed": 0, "total_ms": 0}

    def set(self, **kw):
        self.rec.update(kw)

    def llm(self, model: str, prompt: int = 0, completion: int = 0, cached: int = 0):
        r = self.rec
        r["llm_calls"] += 1
        if model and model not in r["models"]:
            r["models"].append(model)
        r["prompt_tokens"] += int(prompt or 0)
        r["completion_tokens"] += int(completion or 0)
        r["cached_tokens"] += int(cached or 0)
        r["est_cost_usd"] = round(r["est_cost_usd"] + est_cost(model, prompt or 0, completion or 0, cached or 0), 8)

    def stage_add(self, name: str, ms: float):
        self.rec["stages_ms"][name] = round(self.rec["stages_ms"].get(name, 0) + ms, 1)


def start(endpoint: str, question: str = "", lang: str = "en") -> Trace:
    t = Trace(endpoint, question, lang)
    _current.set(t)
    return t


def current() -> Trace | None:
    return _current.get()


@contextlib.contextmanager
def stage(name: str):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        tr = current()
        if tr:
            tr.stage_add(name, (time.perf_counter() - t0) * 1000)
        if name == "llm" and _tr.current():
            _tr.current().llm_ms += int((time.perf_counter() - t0) * 1000)


def set(**kw):  # noqa: A001
    c = _tr.current()
    if c is not None:
        if "route" in kw and kw["route"]:
            _tr.set_route(kw["route"])
        if "intents" in kw:
            c.intents = list(kw["intents"] or [])
        if kw.get("cache_hit") in ("exact", "semantic"):
            c.cache_hit = kw["cache_hit"]
    tr = current()
    if tr:
        tr.set(**kw)


def usage(model: str, um) -> None:
    """Record one LLM call from a google-genai usage_metadata object or a langchain usage dict."""
    tr = current()
    if not tr:
        return
    if um is None:
        tr.llm(model)
    elif isinstance(um, dict):  # langchain: {input_tokens, output_tokens, input_token_details:{cache_read}}
        cached = (um.get("input_token_details") or {}).get("cache_read") or 0
        tr.llm(model, um.get("input_tokens") or 0, um.get("output_tokens") or 0, cached)
    else:
        out = (getattr(um, "candidates_token_count", 0) or 0) + (getattr(um, "thoughts_token_count", 0) or 0)
        tr.llm(model, getattr(um, "prompt_token_count", 0) or 0, out, getattr(um, "cached_content_token_count", 0) or 0)


def embed_call(n_texts: int = 1, chars: int = 0) -> None:
    tr = current()
    if tr:
        tr.rec["embed_calls"] += 1
        tr.rec["est_cost_usd"] = round(tr.rec["est_cost_usd"] + est_cost("gemini-embedding-001", chars // 4, 0), 8)


def finish(tr: Trace | None) -> dict | None:
    if tr is None or tr.rec.get("_done"):
        return None
    tr.rec["_done"] = True
    tr.rec["total_ms"] = int((time.perf_counter() - tr.t0) * 1000)
    rec = {k: v for k, v in tr.rec.items() if k != "_done"}
    with _lock:
        _ring.append(rec)
        if not _testing():
            try:
                p = log_path()
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception:  # noqa: BLE001
                pass
    return rec


def recent(n: int = 100) -> list[dict]:
    with _lock:
        return list(_ring)[-n:]


def stats(n: int = 100) -> dict:
    rows = recent(n)
    if not rows:
        return {"n": 0, "cost_is_estimate": True}

    def med(xs):
        return round(statistics.median(xs), 1) if xs else 0

    lat = sorted(r["total_ms"] for r in rows)
    by_route: dict = {}
    for r in rows:
        b = by_route.setdefault(r["route"] or "?", {"n": 0, "median_ms": [], "llm_calls": 0})
        b["n"] += 1
        b["median_ms"].append(r["total_ms"])
        b["llm_calls"] += r["llm_calls"]
    for b in by_route.values():
        b["median_ms"] = med(b["median_ms"])
    stage_names = {k for r in rows for k in r["stages_ms"]}
    return {
        "n": len(rows),
        "median_ms": med(lat),
        "p90_ms": lat[min(len(lat) - 1, int(0.9 * len(lat)))],
        "llm_calls": sum(r["llm_calls"] for r in rows),
        "embed_calls": sum(r["embed_calls"] for r in rows),
        "prompt_tokens": sum(r["prompt_tokens"] for r in rows),
        "completion_tokens": sum(r["completion_tokens"] for r in rows),
        "cached_tokens": sum(r["cached_tokens"] for r in rows),
        "est_cost_usd": round(sum(r["est_cost_usd"] for r in rows), 6),
        "cost_is_estimate": True,
        "cost_note": "Estimated from a static price table in app/ai/telemetry.py; not a bill.",
        "cache_hit_rate": round(sum(r["cache_hit"] != "none" for r in rows) / len(rows), 3),
        "cache_hits": {k: sum(r["cache_hit"] == k for r in rows) for k in ("exact", "semantic")},
        "grounding_removed": sum(r.get("grounding_removed", 0) for r in rows),
        "by_route": by_route,
        "stage_median_ms": {s: med([r["stages_ms"][s] for r in rows if s in r["stages_ms"]]) for s in sorted(stage_names)},
        "models": sorted({m for r in rows for m in r["models"]}),
        "last": rows[-1],
    }


# ---------- feedback ----------
_fb_engine = None
_fb_table = None


def _fb():
    global _fb_engine, _fb_table
    if _fb_engine is None:
        from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, create_engine
        meta = MetaData()
        _fb_table = Table("ai_feedback", meta,
                          Column("id", Integer, primary_key=True, autoincrement=True),
                          Column("created_at", DateTime(timezone=True)),
                          Column("question", Text), Column("answer", Text),
                          Column("rating", Integer), Column("lang", String(8)))
        _fb_engine = create_engine(sqlalchemy_url())
        meta.create_all(_fb_engine)
    return _fb_engine, _fb_table


def save_feedback(question: str, answer: str, rating: int, lang: str) -> int:
    eng, tbl = _fb()
    with eng.begin() as c:
        r = c.execute(tbl.insert().values(created_at=datetime.now(timezone.utc), question=question[:2000],
                                          answer=answer[:8000], rating=rating, lang=(lang or "en")[:8]))
        return int(r.inserted_primary_key[0])


def feedback_counts() -> dict:
    from sqlalchemy import func, select
    eng, tbl = _fb()
    with eng.connect() as c:
        rows = c.execute(select(tbl.c.rating, func.count()).group_by(tbl.c.rating)).all()
    d = {int(k): int(v) for k, v in rows}
    return {"up": d.get(1, 0), "down": d.get(-1, 0)}
