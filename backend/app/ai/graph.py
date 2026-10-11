"""LangGraph agent: classify_intent -> retrieve -> agent (LLM + tools) -> answer_with_citations.
Works without a Gemini key via rules + BM25 + templated answer."""
import json
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from . import citations, rag, telemetry
from .grounding import UNTRUSTED_RULE
from . import config as _cfg
from .config import gemini_key, gemini_keys, gemini_models, is_quota_error, live, mark_dead, mark_exhausted, pairs, should_rotate
from .tools import ALL_TOOLS, run_tool

MAX_TOOL_CALLS = 4
DISCLAIMER = {
    "en": "This is not official guidance. In an emergency, call 911.",
    "es": "Esto no es una guía oficial. En una emergencia, llame al 911.",
    "vi": "Đây không phải hướng dẫn chính thức. Trong trường hợp khẩn cấp, hãy gọi 911.",
    "zh": "这不是官方指南。紧急情况下，请拨打911。",
    "ar": "هذه ليست إرشادات رسمية. في حالات الطوارئ، اتصل بالرقم 911.",
}
T = {  # fixed template sentences (no-key answers); other languages fall back to Spanish-free English
    "es": {"lead": "Esto es lo más útil para su pregunta, según nuestras fuentes (los textos citados están en inglés):",
           "steps": "Qué hacer:", "eng": " (fuente en inglés)",
           "none": "No tengo información con fuente sobre eso. Para inundaciones, consulte weather.gov y a las autoridades locales.",
           "shelter": "No tengo el estado de los refugios en vivo. Durante una tormenta llame al 311 o al 211, o consulte houstonoem.org. En peligro, llame al 911.",
           "danger": "Si está en peligro, llame al 911 ahora. No maneje ni camine por agua de inundación."},
    "vi": {"lead": "Đây là những điều hữu ích nhất cho câu hỏi của bạn (các nguồn trích dẫn bằng tiếng Anh):",
           "steps": "Cần làm:", "eng": " (nguồn tiếng Anh)",
           "none": "Tôi chưa có thông tin có nguồn về việc này. Hãy xem weather.gov và chính quyền địa phương.",
           "shelter": "Tôi không có tình trạng nơi trú ẩn trực tiếp. Khi có bão hãy gọi 311 hoặc 211, hoặc xem houstonoem.org. Nếu nguy hiểm, gọi 911.",
           "danger": "Nếu bạn gặp nguy hiểm, hãy gọi 911 ngay. Không lái xe hoặc đi bộ qua nước lũ."},
    "zh": {"lead": "以下是针对您问题最有用的信息（引用来源为英文）：",
           "steps": "该怎么做：", "eng": "（英文来源）",
           "none": "我没有关于此事的可靠来源信息。请查看 weather.gov 并联系当地官员。",
           "shelter": "我没有实时避难所状态。风暴期间请拨打311或211，或查看 houstonoem.org。遇险请拨打911。",
           "danger": "如有危险，请立即拨打911。不要驾车或步行穿过洪水。"},
    "ar": {"lead": "هذه أهم المعلومات لسؤالك (المصادر المقتبسة بالإنجليزية):",
           "steps": "ما يجب فعله:", "eng": " (مصدر بالإنجليزية)",
           "none": "ليست لدي معلومات موثقة عن ذلك. راجع weather.gov والجهات المحلية.",
           "shelter": "ليست لدي حالة الملاجئ مباشرة. أثناء العاصفة اتصل بـ 311 أو 211 أو راجع houstonoem.org. في الخطر اتصل بـ 911.",
           "danger": "إذا كنت في خطر فاتصل بالرقم 911 الآن. لا تقد ولا تمشِ في مياه الفيضان."},
}


def _t(lang: str, key: str, default: str) -> str:
    return T.get(lang, {}).get(key, default)


SYSTEM = (
    "You are FloodReady Houston's assistant. Answer ONLY from the retrieved context and tool results; "
    "if they do not cover the question, say you don't know. Cite source URLs inline. "
    "Reply in language code '{lang}'. If someone is in danger, tell them to 'Call 911' first. "
    "End with: 'Not official guidance.' Keep answers short and practical. "
    "User location: {loc}. Earlier conversation turns may be provided; use them to resolve follow-ups. "
    + UNTRUSTED_RULE.replace("{", "{{").replace("}", "}}")
)
VOICE_SUFFIX = (
    "\n\nAfter your full answer, add a final line starting exactly with 'SPEAK:' followed by 1-3 short spoken "
    "sentences (under 300 characters) in language '{lang}', plain speech only: no markdown, no URLs, no brackets, "
    "no emojis. Include 'Call 911' only if there is danger."
)
SAY_911 = {"en": "If you are in danger, call 911.", "es": "Si está en peligro, llame al 911.",
           "vi": "Nếu bạn gặp nguy hiểm, hãy gọi 911.", "zh": "如有危险，请拨打911。", "ar": "إذا كنت في خطر فاتصل بالرقم 911."}
MAX_HISTORY, MAX_TURN_CHARS, MAX_SPEAK = 6, 600, 350


def clean_history(history) -> list[dict]:
    """Keep the last <=6 well-formed user/assistant turns, each truncated to 600 chars."""
    out = []
    for h in history or []:
        if isinstance(h, dict):
            role, content = h.get("role"), h.get("content")
        else:
            role, content = getattr(h, "role", None), getattr(h, "content", None)
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            out.append({"role": role, "content": content.strip()[:MAX_TURN_CHARS]})
    return out[-MAX_HISTORY:]


def _qtext(s) -> str:
    """Question plus the recent user turns, so follow-ups keep their topic."""
    prev = [h["content"] for h in s.get("history") or [] if h["role"] == "user"][-2:]
    return " ".join([*prev, s["question"]])


GLOSSARY = [  # non-English keyword -> English retrieval terms (the knowledge base is English)
    (r"seguro de inquilino|bảo hiểm người thuê|租客保险|تأمين المستأجر", "renters insurance separate flood policy cover"),
    (r"seguro|bảo hiểm|保险|تأمين", "insurance 30-day waiting period"),
    (r"espera|chờ|等待|انتظار", "waiting period 30 days"),
    (r"inquilin|alquil|arrend|người thuê|chủ nhà|租|房东|مستأجر|المالك", "renters tenant landlord disclosure lease"),
    (r"compra de (mi )?casa|mua lại|收购|استحواذ|شراء المنزل", "buyout acquisition voluntary Harris County"),
    (r"refugio|albergue|nơi trú|避难|ملجأ|ملاجئ", "shelter evacuation"),
    (r"moho|mốc|霉|عفن", "mold cleanup"),
    (r"estafa|lừa đảo|诈骗|احتيال", "scam contractor fraud"),
    (r"electric|điện|通电|电|كهرباء", "electrical power safety after flood electrician"),
    (r"manejar|conducir|lái xe|开车|驾车|القيادة|قد", "driving through floodwater turn around don't drown"),
    (r"di[aá]lisis|chạy thận|透析|غسيل", "dialysis medical plan"),
    (r"inund|ngập|lũ|洪水|淹|فيضان", "flood"),
]


def rag_text(s) -> str:
    """Query for retrieval: question + English glossary terms so non-English questions hit English chunks."""
    q = _qtext(s)
    if s.get("lang", "en") != "en" or re.search(r"[^\x00-\x7f]", q):
        extra = [e for pat, e in GLOSSARY if re.search(pat, q.lower())]
        if extra:
            q += " " + " ".join(extra)
    return q


def sanitize_speak(text: str, max_len: int = MAX_SPEAK) -> str:
    """Plain spoken text: no markdown, URLs, bracket citations, emojis; capped at max_len."""
    t = re.sub(r"https?://\S+|www\.\S+", "", text or "")
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"[*_`#>~|]+", "", t)
    t = re.sub(r"^\s*(\d+[.)]|[-•])\s+", "", t, flags=re.M)
    t = "".join(ch for ch in t if not (0x1F000 <= ord(ch) <= 0x1FFFF or 0x2600 <= ord(ch) <= 0x27BF or ord(ch) in (0xFE0F, 0x200D)))
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > max_len:
        sents = re.split(r"(?<=[.!?。])\s+", t)
        out = ""
        for sent in sents:
            if out and len(out) + 1 + len(sent) > max_len:
                break
            out = (out + " " + sent).strip()
        t = out if out and len(out) <= max_len else t[:max_len].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return t


def derive_speak(answer: str, lang: str, danger: bool) -> str:
    """Deterministic spoken summary: first actionable step (+ 911 line if danger)."""
    lines = [ln.strip() for ln in (answer or "").splitlines() if ln.strip()]
    skip = ("not official", "esto no es", "đây không", "这不是", "هذه ليست")
    body = [ln for ln in lines if not ln.lower().startswith(skip) and not ln.rstrip().endswith(":")]
    step = next((ln for ln in body if re.match(r"^(\d+[.)]|[-•])\s", ln)), None) or (body[0] if body else "")
    first = sanitize_speak(step, 260)
    sents = re.split(r"(?<=[.!?。])\s+", first)
    first = " ".join(sents[:2]) if first else ""
    if danger and "911" not in first:
        first = (first + " " + SAY_911.get(lang, SAY_911["en"])).strip()
    return sanitize_speak(first)

INTENT_RULES = [
    ("flood_history", r"flood(ed|s|ing)?\b[^.?!]*\b(before|ever|previously|in the past|history)\b|\b(before|ever|history)\b[^.?!]*\bflood|flood history|flood\w*[^.?!]*harvey|harvey[^.?!]*flood|"
                      r"inund\w*[^.?!]*\b(antes|alguna vez|anteriormente|historial|historia)\b|\b(antes|alguna vez|historial)\b[^.?!]*inund|se (ha )?inundado|historial de inundaci\w+"),
    ("zip_insurance", r"(insurance|seguro)[^.?!]*\b(common|here|zip|area|neighbou?rs?|neighbou?rhood|many|comun\w*|com[uú]n|aqu[ií]|zona|c[oó]digo postal)\b|"
                      r"\bclaims?\b[^.?!]*\b(zip|area|here|neighbou?rhood|code)\b|\b(zip|c[oó]digo postal)\b[^.?!]*(claims?|insurance|seguro|reclamos?)|\breclamos?\b|\bnfip claims\b"),
    ("medical_site", r"\b(dialysis|di[aá]lisis)\b|\b(medical|health) (center|centre|facilit\w+|clinic)s?\b|centro (m[eé]dico|de salud)|cl[ií]nica"),
    ("emergency", r"\b(911|emergency|trapped|rescue|drowning|help me|rising water|emergencia|atrapad\w+|ayuda)\b"),
    ("street_flood", None),  # see _is_street_flood (multilingual)
    ("shelter", r"\b(shelters?|evacuat\w*|where (can|do) i (go|stay)|place to stay|pet[- ]friendly|refugios?|albergues?|evacuar|d[oó]nde puedo ir)\b"),
    ("driving", r"\b(route|drive|driving|road|underpass|crossing|commute|safe to go)\b"),
    ("insurance", r"\b(insurance|seguro|nfip|policy|premium|waiting period|coverage|floodsmart|insure)\b"),
    ("recovery", r"\b(after the flood|cleanup|clean up|repair|fema aid|assistance|flooded|damage|mold|claim)\b"),
    ("civic", r"\b(bond|reservoir|who is responsible|311|buyout|drainage|agency|renter)\b"),
    ("risk", r"\b(risk|safe|floodplain|flood zone|fema|elevation|my (home|house|address)|address)\b"),
]
HARVEY_SRC = "https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county"


class State(TypedDict, total=False):
    question: str
    history: list
    voice: bool
    speak: str
    lang: str
    lat: float | None
    lon: float | None
    intent: str
    intents: list
    context: list
    tool_results: dict
    tools_used: list
    answer: str
    sources: list
    generated_by: str


FLOODING_NOW = (r"floods\b|flooding|flooded|rising water|inunda|anega|ngập|lụt|淹|洪水|水灾|فيضان|تفيض|يغمر|تغمر|غمرت|غرق")
PLACE_OR_DO = (r"street|road|block|yard|house|home|neighborhood|what (do|should|can) i|calle|casa|barrio|colonia|qu[eé] hago|"
               r"qu[eé] debo|đường|nhà|làm (gì|sao)|街|路|家|怎么办|怎么做|怎麼辦|شارع|منزل|بيت|ماذا أفعل|ماذا افعل")
NOT_STREET = (r"insurance|policy|zone|seguro|p[oó]liza|bảo hiểm|保险|تأمين|map|buy-?outs?|rent|tenant|landlord|lease|mold|scam|"
              r"after|before|ever|history|compra|inquilin|arrend|despu[eé]s|antes|alguna vez|mua lại|người thuê|chủ nhà|sau khi|trước|từng|"
              r"收购|租|房东|之后|以前|曾经|استحواذ|مستأجر|المالك|بعد|قبل|سابق")


def _is_street_flood(q: str) -> bool:
    """'My street is flooding / what do I do now', in en/es/vi/zh/ar."""
    return bool(re.search(FLOODING_NOW, q) and re.search(PLACE_OR_DO, q) and not re.search(NOT_STREET, q))


STREET = {  # canned safety steps
    "en": ["If water is rising or you feel unsafe, Call 911 now.",
           "Do not drive or walk through floodwater; it can be deeper and faster than it looks.",
           "Move to a higher floor or higher ground. Do not go into a basement or low area.",
           "Take another route before you leave, and turn on phone emergency alerts and ReadyHarris alerts."],
    "es": ["Si el agua sube o se siente en peligro, llame al 911 ahora.",
           "No maneje ni camine por agua de inundación; puede ser más profunda y rápida de lo que parece.",
           "Suba a un piso más alto o a un lugar elevado. No entre a un sótano ni a una zona baja.",
           "Elija otra ruta antes de salir y active las alertas de emergencia del teléfono y las de ReadyHarris."],
    "vi": ["Nếu nước dâng hoặc bạn thấy không an toàn, hãy gọi 911 ngay.",
           "Không lái xe hoặc đi bộ qua nước lũ; nước có thể sâu và chảy mạnh hơn bạn nghĩ.",
           "Lên tầng cao hơn hoặc nơi cao ráo. Không vào tầng hầm hay khu vực thấp.",
           "Chọn đường khác trước khi ra ngoài và bật cảnh báo khẩn cấp trên điện thoại và ReadyHarris."],
    "zh": ["如果水位上涨或您感到不安全，请立即拨打911。",
           "不要驾车或步行穿过洪水；水可能比看起来更深、更急。",
           "请上到更高的楼层或高地。不要进入地下室或低洼处。",
           "出门前换一条路线，并开启手机紧急警报和 ReadyHarris 警报。"],
    "ar": ["إذا كان الماء يرتفع أو شعرت بعدم الأمان، فاتصل بالرقم 911 الآن.",
           "لا تقد ولا تمشِ في مياه الفيضان؛ فقد تكون أعمق وأسرع مما تبدو.",
           "اصعد إلى طابق أعلى أو مكان مرتفع. لا تدخل القبو أو المناطق المنخفضة.",
           "اختر طريقًا آخر قبل المغادرة وفعّل تنبيهات الطوارئ في هاتفك وتنبيهات ReadyHarris."],
}
STREET_SRC = ["https://digitalcommons.library.tmc.edu/dissertations/AAI1470211",
              "https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system"]


def street_flood_answer(lang: str) -> dict:
    steps = STREET.get(lang, STREET["en"])
    d = rag.card_chunk("driving-in-floods.md", "fact", "77%")
    w = rag.card_chunk("warnings-and-alert-signup.md", "action")
    srcs = [(d or {}).get("source") or STREET_SRC[0], (w or {}).get("source") or STREET_SRC[1]]
    srcs = [u for u in dict.fromkeys(srcs) if u and u.startswith("http")]
    marks = [" [1]", " [1]", " [1]", " [1] [2]"] if len(srcs) > 1 else [" [1]"] * 4
    lines = [f"{i}. {t}{m}" for i, (t, m) in enumerate(zip(steps, marks), 1)]
    lines.append(DISCLAIMER.get(lang, DISCLAIMER["en"]))
    return {"answer": "\n".join(lines), "sources": srcs}


def classify_intent(s: State) -> State:
    q = _qtext(s).lower()
    found = [name for name, pat in INTENT_RULES
             if (_is_street_flood(q) if name == "street_flood" else re.search(pat, q))] or ["general"]
    if "flood_history" in found:  # "has my house flooded before" is history, not a street emergency
        found = [f for f in found if f != "street_flood"]
    return {"intent": found[0], "intents": found}


def retrieve(s: State) -> State:
    return {"context": rag.search(rag_text(s), 4)}


def zip_in_text(q: str) -> str:
    m = re.search(r"(?<!\d)(\d{5})(?!\d)", q or "")
    return m.group(1) if m else ""


def _fallback_tools(s: State) -> list[tuple[str, dict]]:
    """Pick tools to match the detected intents."""
    calls, it = [], set(s.get("intents") or ["general"])
    here = ({"lat": s["lat"], "lon": s["lon"]} if s.get("lat") is not None and s.get("lon") is not None else None)
    if here:
        if it & {"risk", "general", "insurance", "emergency", "driving", "recovery"}:
            calls.append(("get_risk", here))
        if it & {"emergency", "driving", "risk", "general"}:
            calls.append(("get_alerts", here))
        if "civic" in it:
            calls.append(("get_civic", here))
        if "shelter" in it:
            calls.append(("get_shelters", {**here, "pet_friendly": bool(re.search(r"\bpets?\b|dog|cat", _qtext(s).lower()))}))
    if "flood_history" in it and here:
        calls.append(("get_flood_history", {**here, "zip": zip_in_text(_qtext(s))}))
    if "zip_insurance" in it:
        z = zip_in_text(_qtext(s))
        if z:
            calls.append(("get_zip_insurance", {"zip": z}))
    if "medical_site" in it and here:
        calls.append(("get_medical", {**here, "kind": "dialysis", "limit": 3}))
    calls.sort(key=lambda c: c[0] not in ("get_flood_history", "get_zip_insurance", "get_medical"))  # asked-for tools first
    if "insurance" in it and "zip_insurance" not in it:
        calls.append(("insurance_countdown", {"purchase_date": ""}))
    return calls[:MAX_TOOL_CALLS]


def _llm_agent(s: State, model: str, key: str | None = None) -> State:
    """Tool-calling loop with Gemini via langchain-google-genai (async tools run via asyncio)."""
    import asyncio

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    from .routing import tool_json  # compact, untrusted-text-safe tool JSON (lazy: routing imports graph)

    llm = ChatGoogleGenerativeAI(model=model, google_api_key=key or gemini_key(), temperature=0.2)
    llm = llm.bind_tools(ALL_TOOLS)
    loc = f"lat={s['lat']}, lon={s['lon']}" if s.get("lat") is not None and s.get("lon") is not None else "unknown"
    ctx = "\n\n".join(f"[{c['source']}]\n{c['title']}: {c['text']}" for c in s.get("context", []))
    system = SYSTEM.format(lang=s.get("lang", "en"), loc=loc) + (VOICE_SUFFIX.format(lang=s.get("lang", "en")) if s.get("voice") else "")
    msgs = [SystemMessage(system)]
    for h in s.get("history") or []:
        msgs.append(HumanMessage(h["content"]) if h["role"] == "user" else AIMessage(h["content"]))
    msgs.append(HumanMessage(f"Retrieved context:\n{ctx}\n\nQuestion: {s['question']}"))
    results, used, n = {}, [], 0
    while True:
        ai = llm.invoke(msgs)
        telemetry.usage(model, getattr(ai, "usage_metadata", None))
        msgs.append(ai)
        if not ai.tool_calls or n >= MAX_TOOL_CALLS:
            break
        for call in ai.tool_calls:
            n += 1
            if n <= MAX_TOOL_CALLS:
                out = asyncio.run(run_tool(call["name"], call.get("args") or {}))
                used.append(call["name"])
                results[call["name"]] = out
            else:
                out = {"error": "limit"}
            msgs.append(ToolMessage(tool_json(call["name"], out), tool_call_id=call.get("id") or call["name"]))
    text = ai.content if isinstance(ai.content, str) else "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in (ai.content or []))
    text = text.strip()
    if not text:
        raise RuntimeError("empty model answer")  # caller falls back to the template
    spoken = ""
    if s.get("voice"):
        m = re.search(r"(?im)^\W*SPEAK\s*:\s*(.+)\Z", text, flags=re.S)
        if m:
            spoken, text = m.group(1).strip(), text[:m.start()].strip()
        if not text:
            raise RuntimeError("empty model answer")
    return {"answer": text, "speak": spoken, "tool_results": results, "tools_used": used, "generated_by": "gemini"}


async def agent(s: State) -> State:
    if gemini_key():
        import asyncio
        for key, model in pairs(gemini_models()):
            try:
                return await asyncio.to_thread(_llm_agent, s, model, key)
            except Exception as e:
                if not should_rotate(e):
                    break  # fall through to the deterministic path
                # 429 / retired model: mark this (key, model) and try the next pair
                mark_exhausted(key, model, e) if is_quota_error(e) else mark_dead(model, key)
    results, used = {}, []
    for name, args in _fallback_tools(s):
        results[name] = await run_tool(name, args)
        used.append(name)
    return {"tool_results": results, "tools_used": used, "generated_by": "template"}


FLOOD_EVENTS = ("flood", "hurricane", "tropical", "storm surge", "coastal")
ZONE_NOTE = {"X": "minimal mapped hazard", "A": "high-risk", "AE": "high-risk", "AH": "high-risk", "AO": "high-risk",
             "VE": "high-risk coastal", "AR": "high-risk"}


def _trim(text: str, n: int) -> str:
    """Shorten to about n words, always ending on a sentence (or clause) boundary."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text.split()) <= n:
        return text if text.endswith((".", "!", "?")) else text + "."
    sents, out = re.split(r"(?<=[.!?])\s+", text), ""
    for sent in sents:
        if out and len((out + " " + sent).split()) > n:
            break
        out = (out + " " + sent).strip()
    if len(out.split()) > n * 1.6:  # one huge sentence: cut at a clause boundary
        clauses = re.split(r"(?<=[;,:])\s+", out)
        out = ""
        for cl in clauses:
            if out and len((out + " " + cl).split()) > n:
                break
            out = (out + " " + cl).strip()
        out = out.rstrip(",;:")
    return out if out.endswith((".", "!", "?")) else out + "."


class Cites:
    """Numbered citations: the answer shows [n]; URLs go only in the `sources` list."""

    def __init__(self):
        self.urls: list[str] = []

    def __call__(self, url: str) -> str:
        if not url or not url.startswith("http"):
            return ""
        if url not in self.urls:
            self.urls.append(url)
        return f" [{self.urls.index(url) + 1}]"


CUES = [  # (cue name, question regex, card file, chunk kind, keyword)
    # special-needs-and-no-car.md is written by the data lane; cues are skipped until it exists
    ("dialysis", r"\b(dialysis|di[aá]lisis)\b", "special-needs-and-no-car.md", "action", "dialysis"),
    ("no_car_card", r"\b(no car|without a car|don'?t have a car|no vehicle|bus|metro|transit|sin carro|sin auto|sin coche|no tengo (carro|auto|coche))\b", "special-needs-and-no-car.md", "action", ""),
    ("senior_card", r"\b(elderly|older|senior|disabled|wheelchair|mobility|stear|mayor(es)?|anciano\w*|silla de ruedas)\b", "special-needs-and-no-car.md", "action", ""),
    ("medical", r"\b(dialysis|di[aá]lisis|oxygen|ox[ií]geno|ventilator|medical|m[eé]dic\w*|medication|medicina\w*|insulin\w*|chronic|diabet\w*)\b", "vulnerable-households.md", "action", ""),
    ("elderly", r"\b(elderly|older|senior|disabled|disability|wheelchair|mobility|mom|dad|grandm\w+|grandp\w+|parent)\b", "vulnerable-households.md", "action", ""),
    ("scam", r"\b(scam\w*|estafa\w*|gouging|contractor\w*|upfront|up front|fraud|cash only)\b", "post-flood-money-safety.md", "fact", "contractor"),
    ("mold", r"\b(mold|mould|mildew|moho)\b", "post-flood-safety.md", "fact", "mold"),
    ("power", r"\b(power|electric\w*|breakers?|outlets?|electricidad|luz)\b", "post-flood-safety.md", "action", ""),
    ("vin", r"\b(vin|used car|flooded car|flood car|salvage|title wash\w*)\b", "post-flood-money-safety.md", "fact", "vin"),
    ("denied", r"\b(denied|denial|appeal\w*|ineligible|rejected)\b", "post-flood-money-safety.md", "fact", "appeal"),
    ("renter", r"\b(rent|renter|renters|apartment|landlord|lease|tenant|inquilino\w*|alquil\w+|apartamento)\b", "renters-and-buyouts.md", "action", ""),
    ("insurance", r"\b(insurance|insure|coverage|hurricane season|policy|seguro|cobertura|p[oó]liza)\b", "insurance-30-day-and-gap.md", "action", ""),
    ("no_car", r"\b(no car|without a car|don'?t have a car|no vehicle|bus|sin carro|sin auto|sin coche|no tengo (carro|auto|coche))\b", "driving-in-floods.md", "action", ""),
    ("driving", r"\b(drive|driving|underpass|road|manejar|conducir|carretera)\b", "driving-in-floods.md", "action", ""),
    ("language", r"\b(spanish|espa\w+|vietnamese|language|translate|interpreter)\b", "warnings-and-alert-signup.md", "fact", "languages"),
    ("alerts", r"\b(alert|warning|notified|sign up)\b|hurricane season", "warnings-and-alert-signup.md", "action", ""),
]


def _cue_steps(question: str, cite: Cites) -> list[str]:
    q, steps, seen = question.lower(), [], set()
    for name, pat, file, kind, kw in CUES:
        if len(steps) >= 4 or not re.search(pat, q):
            continue
        c = rag.card_chunk(file, kind, kw)
        key = (file, kind)
        if not c or key in seen:
            continue
        seen.add(key)
        text = c["text"].strip()
        text = text[0].upper() + text[1:]
        text = re.sub(r"\s*In an emergency, call 911\.?$", "", text)
        steps.append(_trim(text, 26) + cite(c["source"]))
    return steps


def _lead(s: State, cite: Cites) -> list[str]:
    """Sentences built from tool results (lead of the template answer)."""
    res, parts = s.get("tool_results", {}), []
    es = s.get("lang") == "es"
    hist = res.get("get_flood_history")
    if isinstance(hist, dict) and "error" not in hist:
        h = hist.get("harvey") or {}
        if h.get("flooded") is True:
            parts.append(("Este lugar quedó dentro del área inundada por Harvey en 2017" if es
                          else "This location was inside the area flooded by Hurricane Harvey in 2017") + cite(str(h.get("source", ""))) + ".")
        elif h.get("flooded") is False:
            parts.append(("Este lugar no aparece dentro del área inundada por Harvey en 2017" if es
                          else "This location is not in the mapped Harvey (2017) flood area") + cite(str(h.get("source", ""))) + ".")
        evs = [e for e in hist.get("events") or [] if isinstance(e.get("nearest_gauge"), dict)]
        evs.sort(key=lambda e: -(e["nearest_gauge"].get("peak_ft") or 0))
        for e in evs[:2]:
            g = e["nearest_gauge"]
            parts.append((f"En {e.get('name')}, el medidor {g.get('name')} ({g.get('distance_mi')} mi) llegó a {g.get('peak_ft')} ft ({g.get('peak_category')})." if es
                          else f"In {e.get('name')}, the nearest gauge, {g.get('name')} ({g.get('distance_mi')} mi away), peaked at {g.get('peak_ft')} ft ({g.get('peak_category')})."))
        z = hist.get("zip")
        if isinstance(z, dict):
            parts.append(f"ZIP {z.get('zip')}: NFIP claims peaked in {z.get('peak_year')} ({z.get('peak_year_claims')} claims).")
        parts.append("Gauge peaks are not a map of your street; they only show how high nearby rivers got." if not es
                     else "Los picos de los medidores no son un mapa de su calle; solo muestran cuánto subieron los ríos cercanos.")
    zi = res.get("get_zip_insurance")
    if isinstance(zi, dict) and "error" not in zi:
        cl = zi.get("claims") or {}
        if zi.get("warnings") and not cl.get("total"):
            parts.append(f"I could not get NFIP claims data for ZIP {zi.get('zip')} right now; zero here would mean unknown, not safe." + cite(str(zi.get("source", ""))))
        else:
            pol = zi.get("policies_in_force")
            parts.append((f"En el código postal {zi.get('zip')} hay {cl.get('total')} reclamos NFIP en total ({cl.get('since_2017')} desde 2017)" if es
                          else f"ZIP {zi.get('zip')} has {cl.get('total')} NFIP flood claims on record, {cl.get('since_2017')} since 2017")
                         + (f", and {pol} policies in force" if pol is not None and not es else "") + cite(str(zi.get("source", ""))) + ".")
    elif "zip_insurance" in (s.get("intents") or []) and not zip_in_text(s.get("question", "")):
        parts.append("Tell me your 5-digit ZIP code and I can look up flood insurance claims there." if not es
                     else "Dígame su código postal de 5 dígitos para buscar los reclamos de seguro de inundación.")
    med = res.get("get_medical")
    if isinstance(med, dict) and "error" not in med:
        fac = [f for f in med.get("facilities") or [] if f.get("name")][:3]
        if fac:
            parts.append(("Centros de diálisis cercanos: " if es else "Nearest dialysis centers: ")
                         + "; ".join(f"{f['name']} ({f.get('distance_mi')} mi{', ' + str(f['phone']) if f.get('phone') else ''})" for f in fac)
                         + ". " + str(med.get("note", "")) + cite(str(med.get("source", ""))))
        else:
            parts.append(str(med.get("note", "")) + cite(str(med.get("source", ""))))
    risk = res.get("get_risk")
    if isinstance(risk, dict) and "error" not in risk:
        z = risk.get("fema_zone")
        if z:
            note = ZONE_NOTE.get(str(z).upper(), "")
            sent = f"Your location is in FEMA zone {z}" + (f" ({note})" if note else "")
            if not risk.get("sfha"):
                sent += "; still, about half of Harvey-flooded Harris County homes were outside mapped floodplains" + cite(HARVEY_SRC)
            parts.append(sent.rstrip(".") + ".")
        else:
            parts.append("FEMA zone data was unavailable for this location.")
        if risk.get("low_ground"):
            parts.append("It is low ground relative to nearby gauges.")
        g = (risk.get("nearest_gauges") or [None])[0]
        if isinstance(g, dict):
            parts.append(f"Nearest gauge: {g.get('name')}, status {g.get('status', 'unknown')}"
                         + citations.asof_phrase(risk, s.get("lang", "en")) + ".")
    al = res.get("get_alerts")
    if isinstance(al, dict) and "error" not in al and not al.get("warnings"):
        items = [a for a in al.get("alerts") or []
                 if any(k in str(a.get("event", "")).lower() for k in FLOOD_EVENTS)]
        ph = citations.asof_phrase(al, s.get("lang", "en"))
        parts.append(f"Active NWS alert: {items[0].get('headline', items[0].get('event'))}{ph}." if items
                     else f"No active flood-related NWS alerts here right now{ph}.")
    ins = res.get("insurance_countdown")
    if isinstance(ins, dict) and "error" not in ins and ins.get("effective_date"):
        parts.append(f"Flood insurance takes 30 days to start; buy today and you are covered from "
                     f"{ins['effective_date']}" + cite(ins.get("source", "")) + ".")
    sh = res.get("get_shelters")
    if isinstance(sh, dict) and "error" not in sh:
        parts.append(_t(s.get("lang", "en"), "shelter", "I don't have live shelter status. During a storm call 311 or 211, "
                     "or check houstonoem.org for open shelters. In danger, call 911."))
        names = [str(x.get("name")) for x in (sh.get("shelters") or [])[:2] if x.get("name")]
        if names and s.get("lang", "en") == "en":
            parts.append("Sites used during Harvey near you included " + " and ".join(names) + " (2017, historical)"
                         + cite(str(sh.get("source", ""))) + ".")
    civ = res.get("get_civic")
    if isinstance(civ, dict) and "error" not in civ:
        facts = (civ.get("bond") or {}).get("facts") or []
        if facts and isinstance(facts[0], dict):
            parts.append(_trim(facts[0].get("text", ""), 25) + cite(str(facts[0].get("source", ""))))
    return parts


def SHELTER_NOTE(lang: str) -> str:
    """Shelter status is never live here; always say so and point to 311/211."""
    return _t(lang, "shelter", "I don't have live shelter status; any shelter list here is historical (Harvey, 2017). "
              "During a storm call 311 or 211, or check houstonoem.org for open shelters. In danger, call 911.")


def _tool_sources(x) -> set:
    """URLs that appear under a 'source' key in tool results."""
    out = set()
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "source" and isinstance(v, str) and v.startswith("http"):
                out.add(v)
            else:
                out |= _tool_sources(v)
    elif isinstance(x, list):
        for i in x:
            out |= _tool_sources(i)
    return out


def answer_with_citations(s: State) -> State:
    out = _answer(s)
    if s.get("voice"):
        danger = bool({"emergency", "street_flood"} & set(s.get("intents") or []))
        spoken = sanitize_speak(s.get("speak", "")) if s.get("generated_by") == "gemini" else ""
        if danger and spoken and "911" not in spoken:
            spoken = sanitize_speak(spoken + " " + SAY_911.get(s.get("lang", "en"), SAY_911["en"]))
        out["speak"] = spoken or derive_speak(out["answer"], s.get("lang", "en"), danger)
    return out


def _answer(s: State) -> State:
    ctx = s.get("context", [])
    lang = s.get("lang", "en")
    disclaimer = DISCLAIMER.get(lang, DISCLAIMER["en"])
    allowed = {c["source"] for c in ctx if c["source"].startswith("http")}
    if s.get("generated_by") == "gemini" and s.get("answer"):
        answer = s["answer"]
        found = [u.rstrip(".,)") for u in re.findall(r"https?://[^\s\]\[()<>]+", answer)]
        tool_sources = _tool_sources(s.get("tool_results", {}))
        sources = [u for u in dict.fromkeys(found) if u in allowed or u in tool_sources] or sorted(allowed)[:3]
        for u in dict.fromkeys(found):  # drop invented URLs from the visible text
            if u not in allowed and u not in tool_sources:
                answer = answer.replace(u, "")
        if "911" not in answer and s.get("intent") == "emergency":
            answer = "Call 911. " + answer
        return {"answer": answer, "sources": sources}
    if "street_flood" in (s.get("intents") or []):
        return street_flood_answer(lang)
    # templated answer: tool results first, then profile-matched steps / knowledge facts
    cite = Cites()
    lines = []
    if s.get("intent") == "emergency":
        lines.append(_t(lang, "danger", "If you are in danger, Call 911 now. Do not drive or walk into floodwater."))
    lead = _lead(s, cite)
    if "shelter" in (s.get("intents") or []) and "get_shelters" not in s.get("tool_results", {}):
        lead.append(SHELTER_NOTE(lang))
    if lead:
        lines.append(" ".join(lead))
    elif lang != "en" and lang in T:
        lines.append(T[lang]["lead"])  # localized lead before the English-source bullets
    mark = _t(lang, "eng", "")
    steps = _cue_steps(_qtext(s), cite)
    if steps:
        lines.append(_t(lang, "steps", "What to do:"))
        lines += [f"{i}. {t}{mark}" for i, t in enumerate(steps, 1)]
    else:
        facts = [c for c in ctx if c["source"].startswith("http")][:2]
        lines += [f"- {_trim(c['text'], 24)}{mark}{cite(c['source'])}" for c in facts]
    if not steps and not lead and not ctx:
        lines.append(_t(lang, "none", "I don't have sourced information on that. For flooding, check weather.gov and local officials."))
    lines.append(disclaimer if lang != "en" else "Not official guidance. In danger, call 911.")
    return {"answer": "\n".join(lines), "sources": cite.urls}


def build_graph():
    g = StateGraph(State)
    g.add_node("classify_intent", classify_intent)
    g.add_node("retrieve", retrieve)
    g.add_node("agent", agent)
    g.add_node("answer_with_citations", answer_with_citations)
    g.add_edge(START, "classify_intent")
    g.add_edge("classify_intent", "retrieve")
    g.add_edge("retrieve", "agent")
    g.add_edge("agent", "answer_with_citations")
    g.add_edge("answer_with_citations", END)
    return g.compile()


_graph = None


async def ask(question: str, lang: str = "en", lat: float | None = None, lon: float | None = None,
              history: list | None = None, mode: str | None = None) -> dict[str, Any]:
    global _graph
    _graph = _graph or build_graph()
    out = await _graph.ainvoke({"question": question, "lang": lang or "en", "lat": lat, "lon": lon,
                                "history": clean_history(history), "voice": mode == "voice"})
    res = citations.attach({
        "answer": out["answer"],
        "sources": out.get("sources", []),
        "generated_by": out.get("generated_by", "template"),
        "tools_used": out.get("tools_used", []),
    })
    if mode == "voice":
        res["speak"] = out.get("speak") or derive_speak(out["answer"], lang or "en", False)
    return res
