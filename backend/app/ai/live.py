"""Gemini Live backend (voice engine B, Voice v2): context preload, config, tools, system prompt, model fallback.

SDK feature check (google-genai 2.29, verified by introspection + scripts/bench_live.py probes):
- LiveConnectConfig: realtime_input_config, session_resumption, context_window_compression, input/output
  transcription, speech_config, proactivity, enable_affective_dialog -- all present.
- AutomaticActivityDetection: start/end_of_speech_sensitivity, prefix_padding_ms, silence_duration_ms, disabled.
- Manual turns: send_realtime_input(activity_start=ActivityStart(), activity_end=ActivityEnd()).
- FunctionDeclaration.behavior = NON_BLOCKING and FunctionResponse.scheduling (SILENT/WHEN_IDLE/INTERRUPT) exist.
  Whether a model accepts them is per model: see MODEL_FEATURES (filled from the probe in docs/eval/live-bench.md).
- LiveServerMessage.voice_activity (ACTIVITY_START/END) exists and is used for user_end when the server sends it.
"""
import asyncio
import base64
import binascii
import contextlib
import json
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from app.ai import tools as ai_tools
from app.ai.config import gemini_key
from app.ai.grounding import UNTRUSTED_RULE, sanitize_untrusted, wrap_untrusted

DEFAULT_MODEL = "gemini-3.8-live"
FALLBACK_MODELS = ("gemini-3.1-flash-live-preview", "gemini-2.5-flash-native-audio-latest")
MAX_CONNECTIONS = 4
PRELOAD_BUDGET_S = 1.5
VOICE_NAME = "Kore"

LANG_NAMES = {"en": "English", "es": "Spanish", "vi": "Vietnamese", "zh": "Chinese", "fr": "French",
              "ar": "Arabic", "hi": "Hindi", "ko": "Korean", "tl": "Tagalog", "ur": "Urdu"}

# Per-model feature support (probed by scripts/bench_live.py). Unknown models get the conservative default.
# non_blocking: accepts FunctionDeclaration.behavior=NON_BLOCKING; affective/proactive: v1alpha native-audio extras.
MODEL_FEATURES: dict[str, dict[str, bool]] = {
    # probe 2026-10-11: NON_BLOCKING accepted by all three; affective dialog only on 2.5 native audio (3.x -> 1007);
    # proactivity only on api_version v1alpha (v1beta -> 1007 unknown field), so it stays opt-in via LIVE_PROACTIVE=1.
    "gemini-3.8-live": {"non_blocking": True, "affective": False, "proactive": False},
    "gemini-3.1-flash-live-preview": {"non_blocking": True, "affective": False, "proactive": False},
    "gemini-2.5-flash-native-audio-latest": {"non_blocking": True, "affective": True, "proactive": False},
}
# Median end-of-input -> first-audio latency (ms) from docs/eval/live-bench.md, sent in the ready event.
LATENCY_HINT_MS: dict[str, int] = {
    "gemini-3.1-flash-live-preview": 1424, "gemini-3.8-live": 1681, "gemini-2.5-flash-native-audio-latest": 3828,
}

# Tool -> short label shown to the user while it runs; scheduling of NON_BLOCKING results.
TOOL_LABELS = {
    "get_risk": "Checking flood risk", "get_flood_history": "Looking up flood history",
    "get_zip_insurance": "Checking insurance claims", "get_alerts": "Checking weather alerts",
    "get_medical": "Finding medical facilities", "check_route": "Checking the route",
    "search_knowledge": "Searching flood guides", "get_reservoir_pool": "Checking the reservoir pool",
    "get_declarations": "Checking FEMA declarations", "get_rain": "Checking recent rainfall",
    "get_nri": "Checking FEMA risk index", "get_power_dependent": "Checking power-dependent residents",
    "get_parking": "Checking parking flood risk",
}
URGENT_TOOLS = {"get_alerts", "check_route"}  # results interrupt filler speech


# ---------- env ----------

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def max_session_seconds() -> int:
    return _env_int("LIVE_MAX_SESSION_S", 600)


def live_models() -> list[str]:
    """GEMINI_LIVE_MODEL first, then the fallbacks; models whose every key is exhausted go last."""
    from .config import live_model_list, is_exhausted, gemini_keys
    ms = live_model_list()
    keys = gemini_keys()
    ok = [m for m in ms if not keys or any(not is_exhausted(k, m) for k in keys)]
    return ok + [m for m in ms if m not in ok]


def features(model: str) -> dict[str, bool]:
    base = {"non_blocking": False, "affective": False, "proactive": False}
    base.update(MODEL_FEATURES.get(model.removeprefix("models/"), {}))
    for k in base:  # env override, e.g. LIVE_NON_BLOCKING=1
        v = os.getenv(f"LIVE_{k.upper()}", "").strip().lower()
        if v in {"1", "true", "on"}:
            base[k] = True
        elif v in {"0", "false", "off"}:
            base[k] = False
    return base


def _sens(kind: str, default: str):
    v = os.getenv(f"LIVE_VAD_{kind}_SENSITIVITY", default).strip().lower()
    enum = types.StartSensitivity if kind == "START" else types.EndSensitivity
    return getattr(enum, f"{kind}_SENSITIVITY_{'LOW' if v == 'low' else 'HIGH'}")


def realtime_input_config(manual: bool = False) -> types.RealtimeInputConfig:
    """Snappy automatic VAD (env-tunable), or manual activity start/end for push-to-talk."""
    if manual:
        aad = types.AutomaticActivityDetection(disabled=True)
    else:
        aad = types.AutomaticActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=_sens("START", "high"),
            end_of_speech_sensitivity=_sens("END", "high"),
            prefix_padding_ms=_env_int("LIVE_VAD_PREFIX_MS", 200),
            silence_duration_ms=_env_int("LIVE_VAD_SILENCE_MS", 600),
        )
    return types.RealtimeInputConfig(
        automatic_activity_detection=aad,
        activity_handling=types.ActivityHandling.START_OF_ACTIVITY_INTERRUPTS,
        turn_coverage=types.TurnCoverage.TURN_INCLUDES_ONLY_ACTIVITY,
    )


# ---------- context preload ----------

ZIP_RE = re.compile(r"\b(7[57]\d{3})\b")


def decode_profile(raw: Optional[str]) -> Optional[dict]:
    """profile= is base64(JSON) (urlsafe or standard, padding optional). Returns a dict or None."""
    if not raw:
        return None
    s = raw.strip()
    s += "=" * (-len(s) % 4)
    for dec in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            obj = json.loads(dec(s).decode("utf-8"))
            return obj if isinstance(obj, dict) else None
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
    return None


def _zip_from(place: Optional[str], profile: Optional[dict]) -> str:
    for cand in ((profile or {}).get("zip"), place):
        m = ZIP_RE.search(str(cand or ""))
        if m:
            return m.group(1)
    return ""


def _src(url: Any) -> str:
    u = str(url or "")
    m = re.match(r"https?://(?:www\.)?([^/]+)", u)
    return m.group(1) if m else u


def _fmt_risk(r: dict) -> list[str]:
    out = []
    zone = r.get("fema_zone")
    if zone:
        out.append(f"FEMA flood zone {zone}{' (high-risk SFHA)' if r.get('sfha') else ' (outside the mapped high-risk floodplain)'} [FEMA NFHL]")
    if r.get("elevation_ft") is not None:
        out.append(f"Ground elevation about {r['elevation_ft']} ft [{r.get('elevation_source') or 'USGS'}]")
    if r.get("jurisdiction"):
        out.append(f"Jurisdiction: {r['jurisdiction']}")
    if r.get("reservoir_area"):
        out.append("Inside a reservoir flood pool area (Addicks/Barker)")
    h = r.get("harvey") or {}
    if h.get("flooded") is True:
        out.append(f"Inside the mapped Hurricane Harvey flood extent [{_src(h.get('source'))}]")
    elif h.get("flooded") is False:
        out.append(f"Not inside the mapped Harvey riverine extent (street flooding not mapped) [{_src(h.get('source'))}]")
    for g in (r.get("nearest_gauges") or [])[:2]:
        fs = g.get("flood_stages") or {}
        out.append(f"Gauge {g.get('name')}: {g.get('stage_ft')} ft, status {g.get('status')}, minor flood stage "
                   f"{fs.get('minor')} ft, observed {g.get('observed_at')} [NOAA NWPS]")
    for f in (r.get("facts") or [])[:2]:
        if isinstance(f, dict) and f.get("text"):
            out.append(f"{f['text']} [{_src(f.get('source'))}]")
    return out


def _fmt_history(h: dict) -> list[str]:
    out = []
    for e in (h.get("events") or [])[:4]:
        g = e.get("nearest_gauge") or {}
        out.append(f"{e.get('name')} ({str(e.get('start', ''))[:4]}): nearest gauge {g.get('name')} "
                   f"({g.get('distance_mi')} mi) peaked {g.get('peak_ft')} ft, {g.get('peak_category')} [NOAA/USGS gauge record]")
    z = h.get("zip") or {}
    if z.get("peak_year"):
        out.append(f"ZIP {z.get('zip')} peak claims year {z['peak_year']} ({z.get('peak_year_claims')} claims) [OpenFEMA]")
    return out


def _fmt_claims(c: dict) -> list[str]:
    cl = c.get("claims") or {}
    if not cl:
        return []
    by = sorted(cl.get("by_year") or [], key=lambda x: -(x.get("count") or 0))[:3]
    top = ", ".join(f"{x['year']}: {x['count']}" for x in by)
    s = (f"ZIP {c.get('zip')}: {cl.get('total')} NFIP flood claims total, {cl.get('since_2017')} since 2017"
         f"{'; biggest years ' + top if top else ''}")
    if c.get("policies_in_force") is not None:
        s += f"; about {c['policies_in_force']} policies in force"
    p = c.get("premiums") or {}
    if p.get("median_annual"):
        s += f"; median annual premium ${p['median_annual']}"
    return [s + " [OpenFEMA NFIP]"]


def _fmt_alerts(a: dict) -> list[str]:
    al = a.get("alerts") or []
    if not al:
        return ["No active National Weather Service alerts right now [NWS]"]
    out = []
    for x in al[:3]:
        if isinstance(x, dict):
            out.append(f"ACTIVE ALERT: {x.get('event') or x.get('headline')}"
                       f"{' until ' + str(x.get('ends') or x.get('expires')) if (x.get('ends') or x.get('expires')) else ''} [NWS]")
    return out


def _fmt_profile(p: dict) -> list[str]:
    keep = []
    for k, v in p.items():
        if v in (None, "", [], {}, False) or k in {"lat", "lon", "name", "phone", "email"}:
            continue
        keep.append(f"{sanitize_untrusted(k, 30)}={sanitize_untrusted(json.dumps(v, ensure_ascii=False), 80)}")
    # user-entered values from the URL: data, never instructions
    return ["Household (from the user's saved profile): <untrusted_user_text>"
            + sanitize_untrusted("; ".join(keep[:12]), 1200) + "</untrusted_user_text>"] if keep else []


_CACHE: dict[tuple, tuple[float, dict]] = {}
CACHE_TTL_S = 600.0


def _cache_put(key: tuple, task: "asyncio.Task"):
    with contextlib.suppress(BaseException):
        r = task.result()
        if isinstance(r, dict) and not r.get("error"):
            _CACHE[key] = (time.monotonic(), r)


async def build_context(lat: Optional[float], lon: Optional[float], place: Optional[str] = None,
                        profile: Optional[dict] = None, budget: float = PRELOAD_BUDGET_S) -> str:
    """Fetch risk, flood history, ZIP claims and alerts in parallel (hard budget) -> compact factual block.
    Fetches that miss the budget keep running in the background and fill a 10-minute cache for the next session."""
    calls: dict[str, tuple[str, dict]] = {}
    z = _zip_from(place, profile)
    if lat is not None and lon is not None:
        calls["risk"] = ("get_risk", {"lat": lat, "lon": lon})
        calls["history"] = ("get_flood_history", {"lat": lat, "lon": lon, "zip": z})
        calls["alerts"] = ("get_alerts", {"lat": lat, "lon": lon})
    if z:
        calls["claims"] = ("get_zip_insurance", {"zip": z})
    names = list(calls)
    got: dict[str, dict] = {}
    tasks: dict[asyncio.Task, str] = {}
    now = time.monotonic()
    for n, (tool, args) in calls.items():
        key = (tool, *(round(v, 3) if isinstance(v, float) else v for v in args.values()))
        hit = _CACHE.get(key)
        if hit and now - hit[0] < (120.0 if n == "alerts" else CACHE_TTL_S):
            got[n] = hit[1]
            continue
        t = asyncio.ensure_future(ai_tools.run_tool(tool, args))
        t.add_done_callback(lambda task, key=key: _cache_put(key, task))
        tasks[t] = n
    if tasks:
        done, _pending = await asyncio.wait(set(tasks), timeout=budget)
        for t in done:
            with contextlib.suppress(BaseException):
                r = t.result()
                if isinstance(r, dict) and not r.get("error"):
                    got[tasks[t]] = r
    fmt = {"risk": _fmt_risk, "history": _fmt_history, "claims": _fmt_claims, "alerts": _fmt_alerts}
    lines: list[str] = []
    if place:
        lines.append(f"Place: {wrap_untrusted(place[:120])}")
    for n in ("alerts", "risk", "history", "claims"):
        if n in got:
            try:
                lines += fmt[n](got[n])
            except Exception:  # noqa: BLE001
                pass
    if profile:
        lines += _fmt_profile(profile)
    missing = [n for n in names if n not in got]
    if missing:
        lines.append(f"(Not preloaded, use tools if asked: {', '.join(missing)})")
    return "\n".join(f"- {x}" for x in lines)


# ---------- prompt / tools / config ----------

def system_prompt(lang: str = "en", lat: Optional[float] = None, lon: Optional[float] = None,
                  context: str = "", non_blocking: bool = False) -> str:
    name = LANG_NAMES.get((lang or "en").lower()[:2], lang or "English")
    s = (
        "You are FloodReady Houston, a warm, calm voice assistant helping Houston-area residents prepare for and "
        "get through floods. This is a live spoken conversation: talk like a helpful neighbor, not a document. "
        "Keep each turn to one to three short sentences, plain words, no lists, no markdown, no URLs. "
        "If the user wants more, they will ask. Ask a short clarifying question when needed. "
        f"Start in {name}, but always reply in the language the user is speaking; if they switch, switch with them. "
        "Answer from the SESSION CONTEXT below first; it is fresh data for the user's place. Call a tool only when "
        "the context does not cover the question (another place, routes, medical facilities, insurance details, "
        "general guidance via search_knowledge). Never invent numbers, dates, names or places; if you do not have "
        "it, say so briefly. When it helps trust, mention the source in a few words (for example 'per FEMA'). "
        "If anyone may be in danger, or water is rising inside a home or car, tell them to call 911 right away. "
        "Never drive through flooded roads: turn around, don't drown."
    )
    if non_blocking:
        s += (" Tools run in the background: while waiting, you may say one very short natural phrase, then stop "
              "and wait for the result before giving facts.")
    else:
        s += (" Before calling a tool, first say a very brief natural filler such as 'Let me check that.' "
              "in the user's language, then call it.")
    if lat is not None and lon is not None:
        s += f" The user's location is latitude {lat:.5f}, longitude {lon:.5f}; use it for location tools."
    else:
        s += " The user's location is unknown; ask for an address or ZIP code if a location is needed."
    if context:
        s += (" The SESSION CONTEXT already covers the user's own place: do not call get_risk, get_flood_history, "
              "get_alerts or get_zip_insurance for it unless that item is listed as not preloaded or the user asks "
              "for a refresh or a different place.")
        s += " " + UNTRUSTED_RULE + "\n\nSESSION CONTEXT (sources in brackets):\n" + context
    return s


def _n(desc: str) -> types.Schema:
    return types.Schema(type=types.Type.NUMBER, description=desc)


def _obj(props: dict, req: list[str]) -> types.Schema:
    return types.Schema(type=types.Type.OBJECT, properties=props, required=req)


def tool_declarations(non_blocking: bool = False) -> list[types.FunctionDeclaration]:
    S = types.Schema
    T = types.Type
    latlon = {"lat": _n("Latitude"), "lon": _n("Longitude")}
    b = {"behavior": types.Behavior.NON_BLOCKING} if non_blocking else {}
    return [
        types.FunctionDeclaration(name="get_risk", description="Flood risk score and factors for a location.",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="get_flood_history", description="Past flood events near a location.",
                                  parameters=_obj({**latlon, "zip": S(type=T.STRING, description="ZIP code, optional")},
                                                  ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="get_zip_insurance", description="Flood insurance facts (NFIP) for a ZIP code.",
                                  parameters=_obj({"zip": S(type=T.STRING, description="5-digit ZIP")}, ["zip"]), **b),
        types.FunctionDeclaration(name="get_alerts", description="Active weather and flood alerts at a location.",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(
            name="get_medical", description="Nearby medical facilities (e.g. dialysis) and their flood exposure.",
            parameters=_obj({**latlon, "kind": S(type=T.STRING, description="dialysis, hospital, ..."),
                             "limit": S(type=T.INTEGER, description="max results")}, ["lat", "lon"]), **b),
        types.FunctionDeclaration(
            name="check_route", description="Check whether a driving route crosses flood-prone crossings.",
            parameters=_obj({"origin_lat": _n("Origin latitude"), "origin_lon": _n("Origin longitude"),
                             "dest_lat": _n("Destination latitude"), "dest_lon": _n("Destination longitude")},
                            ["origin_lat", "origin_lon", "dest_lat", "dest_lon"]), **b),
        types.FunctionDeclaration(name="get_reservoir_pool", description="Live Addicks reservoir pool level vs flood stages.",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="get_declarations", description="FEMA disaster declarations / aid status for Harris County.", **b),
        types.FunctionDeclaration(name="get_rain", description="Rain that fell in the last 24-72 hours and the next-24h forecast.",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="get_nri", description="FEMA National Risk Index for the census tract (flood, resilience).",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="get_power_dependent", description="Power-dependent device and oxygen users in a ZIP (emPOWER).",
                                  parameters=_obj({"zip": S(type=T.STRING, description="5-digit ZIP")}, ["zip"]), **b),
        types.FunctionDeclaration(name="get_parking", description="Should I move my car? Parking flood check at a location.",
                                  parameters=_obj(latlon, ["lat", "lon"]), **b),
        types.FunctionDeclaration(name="search_knowledge", description="Search sourced flood knowledge cards.",
                                  parameters=_obj({"query": S(type=T.STRING, description="Search query")}, ["query"]), **b),
    ]


def function_response(fc_id, name: str, out: dict, non_blocking: bool) -> types.FunctionResponse:
    payload = out if "error" in out else {"output": out}
    kw: dict[str, Any] = {"id": fc_id, "name": name, "response": payload}
    if non_blocking:
        kw["scheduling"] = (types.FunctionResponseScheduling.INTERRUPT if name in URGENT_TOOLS
                            else types.FunctionResponseScheduling.WHEN_IDLE)
    return types.FunctionResponse(**kw)


async def execute_tool(name: str, args: dict):
    """Run a declared tool; never raises."""
    try:
        args = dict(args or {})
        if name == "search_knowledge":
            res = await ai_tools.run_tool("search_knowledge", {"query": str(args.get("query", ""))})
        elif name in {d.name for d in tool_declarations()}:
            res = await ai_tools.run_tool(name, args)
        else:
            res = {"error": "unknown tool"}
    except Exception:
        res = {"error": "unavailable"}
    return res if isinstance(res, dict) else {"result": res}


def build_config(lang: str, lat: Optional[float], lon: Optional[float], *, context: str = "", manual: bool = False,
                 resume_handle: Optional[str] = None, model: str = DEFAULT_MODEL) -> types.LiveConnectConfig:
    f = features(model)
    kw: dict[str, Any] = dict(
        response_modalities=[types.Modality.AUDIO],
        system_instruction=system_prompt(lang, lat, lon, context, f["non_blocking"]),
        tools=[types.Tool(function_declarations=tool_declarations(f["non_blocking"]))],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=os.getenv("GEMINI_LIVE_VOICE", VOICE_NAME)))),
        realtime_input_config=realtime_input_config(manual),
        session_resumption=types.SessionResumptionConfig(handle=resume_handle or None),
        context_window_compression=types.ContextWindowCompressionConfig(
            trigger_tokens=_env_int("LIVE_COMPRESS_TRIGGER_TOKENS", 25600),
            sliding_window=types.SlidingWindow(target_tokens=_env_int("LIVE_COMPRESS_TARGET_TOKENS", 12800))),
    )
    if f["affective"]:
        kw["enable_affective_dialog"] = True
    if f["proactive"]:
        kw["proactivity"] = types.ProactivityConfig(proactive_audio=True)
    return types.LiveConnectConfig(**kw)


def make_client():
    key = gemini_key()
    if not key:
        return None
    # proactivity is only accepted on v1alpha
    ver = os.getenv("LIVE_API_VERSION", "").strip() or ("v1alpha" if features(live_models()[0])["proactive"] else "")
    return genai.Client(api_key=key, http_options={"api_version": ver}) if ver else genai.Client(api_key=key)


async def connect_with_fallback(stack, client, lang, lat, lon, *, context: str = "", manual: bool = False,
                                resume_handle: Optional[str] = None, models: Optional[list[str]] = None):
    """Enter client.aio.live.connect on an AsyncExitStack, trying each model. Returns (session, model)."""
    last = None
    for model in models or live_models():
        try:
            cfg = build_config(lang, lat, lon, context=context, manual=manual, resume_handle=resume_handle, model=model)
            sess = await stack.enter_async_context(client.aio.live.connect(model=model, config=cfg))
            return sess, model
        except Exception as e:  # noqa: BLE001
            last = e
            try:
                from .config import should_rotate, is_quota_error, mark_exhausted, mark_dead, gemini_key
                if is_quota_error(e):
                    mark_exhausted(gemini_key(), model, e)
                elif should_rotate(e):
                    mark_dead(model)
            except Exception:  # noqa: BLE001
                pass
            resume_handle = None  # a handle is only valid for the model that issued it
    raise RuntimeError(f"live connect failed: {type(last).__name__}")
