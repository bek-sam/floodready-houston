"""Ask pipeline (typed /ask and SSE /ask/stream):
canned/deterministic answers (no LLM) -> answer cache -> parallel tool prefetch + adaptive RAG ->
ONE Gemini call (lite model, or GEMINI_MODEL for complex questions) -> number grounding -> cache store."""
import asyncio
import json
import os
import re
import time
from typing import Any, AsyncIterator

from . import cache, citations, graph, rag, routing, telemetry, trace
from . import config as _cfg
from .config import (chat_models, complex_models, gemini_key, gemini_keys, is_model_not_found, is_quota_error, live,
                     mark_dead, mark_exhausted, pairs, should_rotate, voice_models)
from .grounding import HEDGE, UNTRUSTED_RULE, evidence_numbers, ground, grounded_sentence
from .tools import run_tool

GAUGE_SRC = "https://api.water.noaa.gov/nwps/v1/"  # live gauge stages (NOAA NWPS), cited for gauge sentences
TOOL_TIMEOUT = 4.0
RAG_TIMEOUT = 4.0
EMBED_TIMEOUT = 1.5
MAX_CHUNK_CHARS = 600
SENT_SPLIT = re.compile(r"(?<=[.!?؟])\s+|(?<=[。！？])")
COMMON = (
    "You are FloodReady Houston's assistant. Answer ONLY from the context and data provided; if they do not cover "
    "the question, say you don't know. Use only numbers that appear in the context or data. " + UNTRUSTED_RULE + " "
    "When you state a live value (river gauge stage/status, active alerts) add the phrase from that tool's \"as_of\" field exactly (e.g. \"as of 3:42 PM CDT\"), and say it is provisional if the field says so. Put a [n] source marker after every sentence that states a fact, number or rule. "
    "If someone is in danger, start with 'Call 911'. Use correct spelling with all accents and diacritics of the "
    "target language. The reply language and user location are given at the top of each request. "
)
FAST_SYSTEM = COMMON + (
    "Speak in 2-4 short plain sentences (each under 200 characters): no markdown, no lists, no URLs, no brackets, "
    "no emojis. Do NOT add any disclaimer. Ignore the instruction about [n] markers: write none."
)
CHAT_SYSTEM = COMMON + (
    "Be practical and complete but concise (a short paragraph or a few short bullet steps). Cite sources with their "
    "bracket numbers: EVERY sentence that states a fact, number, rule or live value must end with its source "
    "marker like [1] (or [1][3]) before the period; never write URLs. End with: 'Not official guidance.' Earlier "
    "conversation turns may be provided; use them to resolve follow-ups."
)
LOC_TOOL_INTENTS = {"risk", "shelter", "civic", "flood_history", "medical_site", "driving", "emergency"}
_bg: set = set()  # background tasks (context-cache creation)


def voice_model() -> str:
    return live(voice_models())[0]


def chat_model() -> str:
    return live(chat_models())[0]


def pick_model(s: dict, voice: bool = False) -> str:
    """Lite model for single-intent questions; GEMINI_MODEL (stronger) for multi-intent or long ones."""
    if routing.complex_question(s) and os.getenv("AI_MODEL_ROUTING", "1") != "0":
        return live(complex_models())[0]  # GEMINI_MODEL, or the next non-exhausted fallback
    return voice_model() if voice else chat_model()


def ask_timeout() -> float:
    try:
        return float(os.getenv("ASK_TIMEOUT_S", "12"))
    except ValueError:
        return 12.0


def _client(types, genai, key: str | None = None):
    """Client with SDK retries off (attempts=1) and a per-request HTTP timeout, so 429s fail fast."""
    ms = int(ask_timeout() * 1000)
    try:
        opts = types.HttpOptions(timeout=ms, retry_options=types.HttpRetryOptions(attempts=1))
    except Exception:  # noqa: BLE001  (older SDK)
        opts = types.HttpOptions(timeout=ms)
    return genai.Client(api_key=key or gemini_key(), http_options=opts)


def sse(obj: dict) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


def split_sentences(buf: str, final: bool = False) -> tuple[list[str], str]:
    """Return (complete sentences, remainder). With final=True the remainder is flushed as a sentence."""
    parts = SENT_SPLIT.split(buf)
    if final:
        return [p for p in parts if p.strip()], ""
    return [p for p in parts[:-1] if p.strip()], parts[-1]


async def _guard(coro, timeout):
    try:
        return await asyncio.wait_for(coro, timeout)
    except Exception:
        return None


async def prefetch(s: dict) -> tuple[dict, list, list]:
    """Intent-matched tools and adaptive RAG, concurrently. Returns (tool_results, used, context)."""
    calls = routing.select_tools(s)
    z = graph.zip_in_text(graph._qtext(s))
    names = [n for n, _ in calls]
    if s.get("lat") is not None and s.get("lon") is not None and "get_flood_history" in names:
        calls = [(n, {**a, "zip": z} if n == "get_flood_history" else a) for n, a in calls]
    if z and "get_zip_insurance" not in names:
        calls.append(("get_zip_insurance", {"zip": z}))
    names = [n for n, _ in calls]

    async def rag_job():
        with telemetry.stage("rag"):
            return await _guard(asyncio.to_thread(rag.search_adaptive, graph.rag_text(s)), RAG_TIMEOUT)

    async def tools_job():
        with telemetry.stage("tools"):
            return await asyncio.gather(*[_guard(run_tool(n, a), TOOL_TIMEOUT) for n, a in calls])

    ctx, outs = await asyncio.gather(rag_job(), tools_job())
    results = {n: r for n, r in zip(names, outs) if isinstance(r, (dict, list)) and not (isinstance(r, dict) and r.get("error"))}
    return results, list(results), ctx or []


def numbered_sources(ctx, results) -> list[str]:
    tool_src = sorted(graph._tool_sources(results))
    ctx_src = [c["source"] for c in ctx if str(c.get("source", "")).startswith("http")]
    gauges = [GAUGE_SRC] if any(g for g in ((results.get("get_risk") or {}).get("nearest_gauges") or [])) else []
    # official tool sources first, then official retrieved chunks, then the rest (blogs/news last)
    allsrc = list(dict.fromkeys(tool_src + gauges + ctx_src))
    return sorted(allsrc, key=lambda u: not is_official(u))  # stable: keeps tool-first order within groups


OFFICIAL_HOSTS = ("fema.gov", "houstontx.gov", "noaa.gov", "weather.gov", "usgs.gov", "hcfcd.org", "harriscountytx.gov")


def is_official(u: str) -> bool:
    m = re.match(r"https?://([^/]+)", u or "")
    h = (m.group(1) if m else "").lower()
    return any(h == d or h.endswith("." + d) for d in OFFICIAL_HOSTS)


def add_tool_citations(answer: str, sources: list[str], tool_srcs, cap: int = 5) -> tuple[str, list[str]]:
    """Append official tool sources not yet cited (only while room under `cap`; existing indexes stay valid) and tag the
    sentence containing Zone/Harvey/ft with [k] when it has no marker."""
    srcs = list(sources)
    extra = [u for u in sorted(tool_srcs) if is_official(u) and u not in srcs]
    for u in extra:
        if len(srcs) < cap:
            srcs.append(u)
    if len(srcs) == len(sources):
        return answer, srcs
    k = len(sources) + 1
    lines = answer.split("\n")
    for i, ln in enumerate(lines):
        parts = re.split(r"(?<=[.!?])\s+", ln)
        for j, sent in enumerate(parts):
            if re.search(r"\bZone\b|Harvey|\d\s?ft\b", sent) and not re.search(r"\[\d+\]", sent):
                parts[j] = re.sub(r"([.!?]?)$", rf" [{k}]\1", sent, count=1)
                lines[i] = " ".join(parts)
                return "\n".join(lines), srcs
    return answer, srcs


def build_prompt(question, history, ctx, results, lang: str = "en", loc: str = "unknown") -> str:
    srcs = numbered_sources(ctx, results)
    num = {u: i for i, u in enumerate(srcs, 1)}
    c = "\n\n".join(f"[{num.get(x['source'], '?')}] {x.get('title', '')}: {x['text'][:MAX_CHUNK_CHARS]}" for x in ctx)
    d = "\n".join(f"{k}: {routing.tool_json(k, v)}" for k, v in results.items())
    s = "\n".join(f"[{i}] {u}" for i, u in enumerate(srcs, 1))
    h = "".join(f"{x['role']}: {x['content']}\n" for x in history)
    return (f"Reply language code: '{lang}'. User location: {loc}.\n\nRetrieved context:\n{c or 'none'}\n\n"
            f"Live data:\n{d or 'none'}\n\nSources:\n{s or 'none'}\n\n{h}Question: {question}")


def _configs(types, system, model: str = "", cached: str | None = None):
    """Thinking minimized. Gemini 2.x takes thinking_budget; newer models take thinking_level. Falls back to the
    other form, then to defaults, if a model rejects a setting."""
    base = dict(cached_content=cached, temperature=0.2) if cached else dict(system_instruction=system, temperature=0.2)
    level = types.GenerateContentConfig(**base, thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"))
    budget = types.GenerateContentConfig(**base, thinking_config=types.ThinkingConfig(thinking_budget=0))
    first = [budget, level] if model.startswith("gemini-2") else [level, budget]
    return [*first, types.GenerateContentConfig(**base)]


def _ctx_cache(client, types, model: str, kind: str, system: str) -> str | None:
    """Live explicit cache name, else start creating one in the background (never blocks the request)."""
    name = cache.ctx_name(model, kind)
    if name or not cache.ctx_enabled() or os.getenv("PYTEST_CURRENT_TEST"):
        return name
    try:
        t = asyncio.get_running_loop().create_task(asyncio.to_thread(cache.ctx_create, client, types, model, kind, system))
        _bg.add(t)
        t.add_done_callback(_bg.discard)
    except Exception:  # noqa: BLE001
        pass
    return None


def _fail_fast(e: Exception) -> bool:
    return any(k in f"{type(e).__name__} {e}".lower() for k in ("429", "resource_exhausted", "timeout", "unavailable"))


async def gemini_stream(system: str, prompt: str, model: str | None = None) -> AsyncIterator[str]:
    """Yield text chunks. Rotates (key, model) pairs on 429/404, trying thinking configs per pair."""
    from google import genai
    from google.genai import types

    last: Exception | None = None
    for key, m in pairs([model, *voice_models()] if model else voice_models()):
        client = _client(types, genai, key)
        cached = _ctx_cache(client, types, m, "voice", system)
        for cfg in _configs(types, system, m, cached):
            started, um = False, None
            try:
                async for chunk in await client.aio.models.generate_content_stream(model=m, contents=prompt, config=cfg):
                    um = getattr(chunk, "usage_metadata", None) or um
                    t = chunk.text if chunk.candidates else ""
                    if t:
                        started = True
                        yield t
                if started:
                    telemetry.usage(m, um)
                    _cfg.last_model.set(m)
                    return
            except Exception as e:  # noqa: BLE001
                telemetry.usage(m, um)
                if started:
                    raise
                last = e
                if cached:
                    cache.ctx_drop(m, "voice")
                    cached = None
                if should_rotate(e):
                    mark_exhausted(key, m, e) if is_quota_error(e) else mark_dead(m, key)
                    break  # next (key, model)
    raise last or RuntimeError("no model produced output")


async def gemini_once(system: str, prompt: str, model: str | None = None) -> str:
    """ONE non-streaming Gemini call (minimal thinking). Rotates (key, model) pairs on 429/404 within the caller's
    timeout budget; other failures try the next thinking config, then fail to the template."""
    from google import genai
    from google.genai import types

    last: Exception | None = None
    for key, m in pairs([model, *chat_models()] if model else chat_models()):
        client = _client(types, genai, key)
        cached = _ctx_cache(client, types, m, "chat", system)
        for cfg in _configs(types, system, m, cached):
            try:
                r = await client.aio.models.generate_content(model=m, contents=prompt, config=cfg)
                telemetry.usage(m, getattr(r, "usage_metadata", None))
                if (r.text or "").strip():
                    _cfg.last_model.set(m)
                    return r.text
            except Exception as e:  # noqa: BLE001
                telemetry.usage(m, None)  # failed call: counts as a call, no tokens
                last = e
                if cached:
                    cache.ctx_drop(m, "chat")
                    cached = None
                if should_rotate(e):
                    mark_exhausted(key, m, e) if is_quota_error(e) else mark_dead(m, key)
                    break  # next (key, model)
                if _fail_fast(e):
                    raise  # slow/unavailable: fail fast to the template
    raise last or RuntimeError("no model produced output")


def _is_disclaimer(t: str) -> bool:
    low = t.lower().strip()
    return low.startswith(("not official guidance", "esto no es una gu", "đây không phải", "这不是官方", "هذه ليست إرشادات"))


def _evidence(s: dict) -> set[str]:
    hist = " ".join(h["content"] for h in s.get("history") or [])
    texts = [c.get("text", "") for c in s.get("context", [])]
    if any(cache.ctx_name(m, k) for m in (chat_model(), voice_model(), complex_models()[0]) for k in ("chat", "voice")):
        texts.append(cache.digest())
    return evidence_numbers(s.get("question", ""), hist, *texts, s.get("tool_results", {}), *citations.asof_texts(s.get("tool_results", {})))


def _renumber(text: str, srcs: list[str]) -> tuple[str, list[str]]:
    """Model cites [n] from the prompt's numbered Sources; keep cited ones, renumber 1..m, drop invalid markers."""
    def expand(m):
        out = []
        for part in re.split(r"\s*[,;]\s*", m.group(1)):
            a, _, b = part.partition("-") if "-" in part else part.partition("–")
            lo, hi = int(a), int(b or a)
            out += [f"[{n}]" for n in range(lo, min(hi, lo + 9) + 1)]
        return "".join(out)
    text = re.sub(r"\[(\d{1,2}(?:\s*[,;–-]\s*\d{1,2})+)\]", expand, text)
    order: list[int] = []
    for m in re.finditer(r"\[(\d{1,2})\]", text):
        n = int(m.group(1))
        if 1 <= n <= len(srcs) and n not in order:
            order.append(n)
    new = {n: i for i, n in enumerate(order, 1)}
    text = re.sub(r"(\s*)\[(\d{1,2})\]", lambda m: f"{m.group(1)}[{new[int(m.group(2))]}]" if int(m.group(2)) in new else "", text)
    return re.sub(r"(\[\d+\])(\s*\1)+", r"\1", text), [srcs[n - 1] for n in order]


def _gemini_final(s: dict, full: str) -> dict:
    """Grounded, citation-filtered answer + localized disclaimer; sources from [n] markers, URLs, tools and chunks."""
    lang = s.get("lang", "en")
    text = re.sub(r"(?is)\s*not official guidance\.?\s*$", "", full.strip()).strip()
    text = re.sub(r"(?i)\s*\[(live data|retrieved context)[^\]]*\]", "", text).strip()
    before = text
    text, removed, warns = ground(text, _evidence(s), lang)
    if removed:
        telemetry.set(grounding_removed=removed)
    emptied = bool(removed) and text.strip() == HEDGE.get(lang, HEDGE["en"]) and before.strip() != text.strip()
    if "shelter" in (s.get("intents") or []) and not re.search(r"311|211|houstonoem", text):
        text += " " + graph.SHELTER_NOTE(lang)  # shelter status is never live: always say so
    srcs = numbered_sources(s.get("context", []), s.get("tool_results", {}))
    cited: list[str] = []
    if re.search(r"\[\d{1,2}(?:\s*[,;–-]\s*\d{1,2})*\]", text):
        text, cited = _renumber(text, srcs)
    out = graph._answer({**s, "generated_by": "gemini", "answer": text})
    if cited:
        out["sources"] = cited + [u for u in out["sources"] if u not in cited and re.search(re.escape(u), text)]
    elif not re.search(r"https?://", text):
        out["sources"] = srcs[:4]
    out["answer"] = re.sub(r"\(\s*\)|\[\s*\]", "", out["answer"])
    res = s.get("tool_results", {})
    out["answer"], out["sources"] = add_tool_citations(out["answer"], out["sources"], graph._tool_sources(res))
    out["answer"], out["sources"] = citations.tag_live(
        out["answer"], out["sources"], "https://api.weather.gov/alerts/active", GAUGE_SRC,
        bool((res.get("get_risk") or {}).get("nearest_gauges")), isinstance(res.get("get_alerts"), dict))
    disc = graph.DISCLAIMER.get(lang, graph.DISCLAIMER["en"]) if lang != "en" else "Not official guidance. In danger, call 911."
    out["answer"] = out["answer"].rstrip() + "\n" + disc
    if warns:
        out["warnings"] = warns
    if emptied:
        out["grounding_empty"] = True  # nothing verifiable left: callers use the template answer instead
    return out


def _state(question, lang, lat, lon, hist, voice) -> dict[str, Any]:
    s: dict[str, Any] = {"question": question, "lang": lang, "lat": lat, "lon": lon, "history": hist, "voice": voice}
    s.update(graph.classify_intent(s))
    telemetry.set(intents=s["intents"])
    return s


async def _cache_lookup(s: dict, mode) -> tuple[str | None, Any, dict | None]:
    """(key, embedding, payload-or-None) for cacheable questions."""
    if not cache.cacheable(s):
        return None, None, None
    k = cache.key(s["question"], s["lang"], mode)
    with telemetry.stage("cache"):
        hit = cache.get_exact(k)
        if hit:
            telemetry.set(cache_hit="exact")
            return k, None, hit
        emb = None
        if gemini_key():
            emb = await _guard(asyncio.to_thread(rag.embed_query, graph.rag_text(s)), EMBED_TIMEOUT)
            sem = cache.get_semantic(k, emb)
            if sem:
                telemetry.set(cache_hit="semantic", cache_sim=round(sem[1], 3))
                return k, emb, sem[0]
    return k, emb, None


def _debug_evidence(s: dict) -> list[str]:
    return ([f"[{c.get('source')}] {c.get('text', '')}" for c in s.get("context", [])]
            + [f"{k}: {routing.tool_json(k, v)}" for k, v in (s.get("tool_results") or {}).items()])


async def stream_ask(question: str, lang: str = "en", lat=None, lon=None, history=None, mode=None) -> AsyncIterator[str]:
    t0 = time.perf_counter()
    col = trace.begin()
    lang = lang or "en"
    hist = graph.clean_history(history)
    first_ms = None

    def ms() -> int:
        return int((time.perf_counter() - t0) * 1000)

    s_ref: list = []

    def final(answer, sources, used, by, warnings=None):
        cit = citations.attach({"answer": answer, "sources": sources}, template=by == "template")
        answer = cit["answer"]
        return sse({"type": "final", "answer": answer, "sources": sources, "tools_used": used, "generated_by": by,
                    "citations": cit["citations"], "uncited": cit["uncited"],
                    **({"warnings": warnings} if warnings else {}),
                    "trace": trace.build(col, by, (s_ref[0].get("context") if s_ref else None)),
                    "timings": {"first_speak_ms": first_ms if first_ms is not None else ms(), "total_ms": ms()}})

    def speak(text):
        nonlocal first_ms
        if first_ms is None:
            first_ms = ms()
        return sse({"type": "speak", "text": text})

    try:
        s = _state(question, lang, lat, lon, hist, True)
        s_ref.append(s)
        danger = bool({"emergency", "street_flood"} & set(s["intents"]))
        if "street_flood" in s["intents"]:  # canned multilingual safety answer, same as /ask
            telemetry.set(route="canned")
            out = graph.street_flood_answer(lang)
            for step in graph.STREET.get(lang, graph.STREET["en"]):
                yield speak(step)
            yield final(out["answer"], out["sources"], [], "template")
            return
        with telemetry.stage("route"):
            det = await routing.deterministic(s, run_tool)
        if det:
            telemetry.set(route=det["route"])
            for sent in split_sentences(graph.derive_speak(det["answer"], lang, False), True)[0]:
                yield speak(sent.strip())
            yield final(det["answer"], det["sources"], det["tools_used"], "template")
            return
        k, emb, hit = (None, None, None) if not gemini_key() else await _cache_lookup(s, "voice")
        if hit:
            telemetry.set(route="cache")
            for sent in hit.get("speak") or []:
                yield speak(sent)
            yield final(hit["answer"], hit["sources"], hit.get("tools_used", []), hit.get("generated_by", "gemini"))
            return
        results, used, ctx = await prefetch(s)
        s["context"], s["tool_results"] = ctx, results
        if gemini_key():
            spoken: list[str] = []
            full = ""
            try:
                model = pick_model(s, voice=True)
                telemetry.set(route="llm_strong" if model != voice_model() else "llm_single")
                loc = f"lat={lat}, lon={lon}" if lat is not None and lon is not None else "unknown"
                prompt = build_prompt(question, hist, ctx, results, lang, loc)
                ev = _evidence(s)
                buf = ""
                with telemetry.stage("llm"):
                    async for text in gemini_stream(FAST_SYSTEM, prompt, model):
                        full += text
                        buf += text
                        sents, buf = split_sentences(buf)
                        for sent in sents:
                            sp = graph.sanitize_speak(sent, 300)
                            if sp and not _is_disclaimer(sp) and grounded_sentence(sp, ev):
                                spoken.append(sp)
                                yield speak(sp)
                    for sent in split_sentences(buf, True)[0]:
                        sp = graph.sanitize_speak(sent, 300)
                        if sp and not _is_disclaimer(sp) and grounded_sentence(sp, ev):
                            spoken.append(sp)
                            yield speak(sp)
                if not full.strip():
                    raise RuntimeError("empty model answer")
                if danger and "911" not in full:
                    extra = graph.SAY_911.get(lang, graph.SAY_911["en"])
                    full = full.strip() + " " + extra
                    spoken.append(extra)
                    yield speak(extra)
                out = _gemini_final(s, full)
                if out.get("grounding_empty") and not spoken:
                    raise RuntimeError("no grounded sentences")  # -> template fallback below
                if k and not danger and not out.get("warnings"):
                    cache.put(k, {"answer": out["answer"], "sources": out["sources"], "tools_used": used,
                                  "generated_by": "gemini", "speak": spoken}, emb)
                yield final(out["answer"], out["sources"], used, "gemini", out.get("warnings"))
                return
            except Exception:  # noqa: BLE001
                if first_ms is not None:  # already spoke: do not repeat; finish with what we have
                    out = _gemini_final(s, full or "-")
                    yield final(out["answer"], out["sources"], used, "gemini")
                    return
        # template fallback
        telemetry.set(route="template")
        for name, args in graph._fallback_tools(s):
            if name not in results:
                r = await _guard(run_tool(name, args), TOOL_TIMEOUT)
                if r is not None:
                    results[name] = r
                    used.append(name)
        s["generated_by"] = "template"
        out = graph.answer_with_citations(s)
        for sent in split_sentences(out.get("speak") or "", True)[0]:
            yield speak(sent.strip())
        yield final(out["answer"], out["sources"], used, "template")
    except Exception:  # noqa: BLE001
        yield sse({"type": "error", "detail": "Sorry, I could not answer right now. In an emergency, call 911."})


async def _template_ask(s: dict, results: dict, used: list, warning: str | None, mode) -> dict:
    telemetry.set(route="template")
    for name, args in graph._fallback_tools(s):
        if name not in results:
            r = await _guard(run_tool(name, args), TOOL_TIMEOUT)
            if r is not None:
                results[name] = r
                used.append(name)
    s = {**s, "tool_results": results, "generated_by": "template"}
    out = graph.answer_with_citations(s)
    res = {"answer": out["answer"], "sources": out.get("sources", []), "generated_by": "template", "tools_used": used}
    if mode == "voice":
        res["speak"] = out.get("speak") or graph.derive_speak(out["answer"], s["lang"], False)
    if warning:
        res["warnings"] = [warning]
    return res


async def ask_once(*a, **kw) -> dict:
    """ask_once_inner + per-sentence citations (`citations`, `uncited`) validated against `sources`."""
    col = trace.begin()
    res = await _ask_once(*a, **kw)
    if isinstance(res, dict):
        res["trace"] = trace.build(col, res.get("generated_by", "template"))
    if isinstance(res, dict) and res.get("answer"):
        citations.attach(res, template=res.get("generated_by") == "template")
        if res["uncited"] and res.get("generated_by") == "gemini":
            telemetry.set(uncited_claims=len(res["uncited"]))
    return res


async def _ask_once(question: str, lang: str = "en", lat=None, lon=None, history=None, mode=None, debug: bool = False) -> dict:
    """Typed-chat /ask: canned + deterministic intents first (no LLM), answer cache, parallel prefetch +
    ONE Gemini call, hard timeout -> template."""
    lang = lang or "en"
    hist = graph.clean_history(history)
    s = _state(question, lang, lat, lon, hist, mode == "voice")
    if "street_flood" in s["intents"]:  # instant canned multilingual answer
        telemetry.set(route="canned")
        out = graph.answer_with_citations({**s, "generated_by": "template", "context": [], "tool_results": {}})
        res = {"answer": out["answer"], "sources": out["sources"], "generated_by": "template", "tools_used": []}
        if mode == "voice":
            res["speak"] = out.get("speak") or graph.derive_speak(out["answer"], lang, True)
        if debug:
            cards = [rag.card_chunk("driving-in-floods.md", "fact", "77%"), rag.card_chunk("warnings-and-alert-signup.md", "action")]
            res["evidence"] = [f"[{c['source']}] {c['text']}" for c in cards if c] + graph.STREET["en"]
        return res
    with telemetry.stage("route"):
        det = await routing.deterministic(s, run_tool)
    if det:
        telemetry.set(route=det["route"])
        res = {"answer": det["answer"], "sources": det["sources"], "generated_by": "template", "tools_used": det["tools_used"]}
        if mode == "voice":
            res["speak"] = graph.derive_speak(det["answer"], lang, False)
        if debug:
            res["evidence"] = det.get("evidence", [])
        return res
    if not gemini_key():
        telemetry.set(route="template")
        return await graph.ask(question, lang, lat, lon, history, mode)
    k, emb, hit = await _cache_lookup(s, mode)
    if hit:
        telemetry.set(route="cache")
        hit = dict(hit)
        ev = hit.pop("_evidence", [])
        return {**hit, **({"evidence": ev} if debug else {})}
    budget = ask_timeout()
    results, used, ctx = await prefetch(s)
    s["context"], s["tool_results"] = ctx, results
    model = pick_model(s)
    telemetry.set(route="llm_strong" if model not in (chat_model(), voice_model()) else "llm_single")
    try:
        loc = f"lat={lat}, lon={lon}" if lat is not None and lon is not None else "unknown"
        with telemetry.stage("llm"):
            full = await asyncio.wait_for(gemini_once(CHAT_SYSTEM, build_prompt(question, hist, ctx, results, lang, loc), model=model), budget)
    except Exception as e:  # noqa: BLE001
        why = f"Gemini timed out after {budget:g}s" if isinstance(e, asyncio.TimeoutError) else f"Gemini unavailable ({type(e).__name__})"
        return await _template_ask(s, results, used, why + "; used template answer.", mode)
    danger = bool({"emergency", "street_flood"} & set(s["intents"]))
    if danger and "911" not in full:
        full = full.strip() + " " + graph.SAY_911.get(lang, graph.SAY_911["en"])
    with telemetry.stage("ground"):
        out = _gemini_final(s, full)
    if out.get("grounding_empty"):
        return await _template_ask(s, results, used, out["warnings"][0] + "; used template answer.", mode)
    res = {"answer": out["answer"], "sources": out["sources"], "generated_by": "gemini", "tools_used": used}
    if out.get("warnings"):
        res["warnings"] = out["warnings"]
    if mode == "voice":
        res["speak"] = graph.derive_speak(out["answer"], lang, danger)
    if k and not danger and not out.get("warnings"):
        cache.put(k, {**res, "_evidence": _debug_evidence(s)}, emb)
    if debug:
        mdl = _cfg.last_model.get()
        res["model"] = mdl
        res["evidence"] = [f"model: {mdl}", *_debug_evidence(s)]
    return res
