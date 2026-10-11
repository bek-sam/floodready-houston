"""Per-sentence citations + answer freshness helpers.

The answer text carries inline [n] markers tied to the `sources` list. `attach` turns them into
`citations:[{sentence_index, source_index}]` (source_index is 0-based into `sources`), drops markers that point
at a source that was not retrieved, and reports factual sentences (numbers/dates) that have no citation."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .grounding import ALWAYS_OK, SENT_RE, numbers

MARK = re.compile(r"\[(\d{1,2})\]")
MARKS_ONLY = re.compile(r"^(?:\s*\[\d{1,2}\])+\s*[.!?]?$")
LIST_PREFIX = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+")
LIVE = re.compile(r"\(as of |\bas of \d|\bal \d|tính đến|截至|حتى ", re.I)  # live tool value: backed by the tool, stamped with its time
DISCLAIMERS = ("not official guidance", "esto no es una gu", "đây không phải", "这不是官方", "هذه ليست إرشادات")
TZ = ZoneInfo("America/Chicago")
ASOF = {"en": "as of {t}", "es": "al {t}", "vi": "tính đến {t}", "zh": "截至 {t}", "ar": "حتى {t}"}
PROVISIONAL = {"en": "provisional", "es": "provisional", "vi": "tạm thời", "zh": "临时数据", "ar": "مؤقتة"}


def _split(answer: str) -> list[tuple[str, int]]:
    """(sentence, line number) in reading order; a lone '[n]' piece joins the previous sentence."""
    out: list[list] = []
    for li, line in enumerate((answer or "").split("\n")):
        body = LIST_PREFIX.sub("", line).strip()
        for s in SENT_RE.split(body) if body else []:
            if not s.strip():
                continue
            if out and MARKS_ONLY.match(s.strip()):
                out[-1][0] += " " + s.strip()
            else:
                out.append([s.strip(), li])
    return [(s, li) for s, li in out]


def sentences(answer: str) -> list[str]:
    return [s for s, _ in _split(answer)]


def is_factual(s: str) -> bool:
    """A sentence with a checkable claim: a number other than emergency numbers/list counts."""
    low = s.lower()
    if low.startswith(DISCLAIMERS) or ("911" in s and not [n for n in numbers(s) if n not in ALWAYS_OK]):
        return False
    return any(n not in ALWAYS_OK for n in numbers(s))


def attach(res: dict, template: bool = False) -> dict:
    """Add `citations` and `uncited` (sentence indices of factual sentences without a valid citation) to a response."""
    answer, srcs = res.get("answer") or "", res.get("sources") or []

    answer = re.sub(r"(\s*)\[(\d{1,2})\]", lambda m: m.group(0) if 1 <= int(m.group(2)) <= len(srcs) else "", answer)
    res["answer"] = answer
    cites, uncited = [], []
    last: dict[int, list[int]] = {}  # template answers: a line is built from one tool/source, so it shares its citation
    for i, (s, li) in enumerate(_split(answer)):
        seen = []
        for m in MARK.finditer(s):
            n = int(m.group(1))
            if 1 <= n <= len(srcs) and n - 1 not in seen:
                seen.append(n - 1)
        if seen:
            last[li] = seen
        elif template and li in last:
            seen = last[li]
        cites += [{"sentence_index": i, "source_index": n} for n in seen]
        if not seen and is_factual(s) and not LIVE.search(s):
            uncited.append(i)
    res["citations"] = cites
    res["uncited"] = uncited
    return res


# ---------- freshness ----------
def local_time(iso, lang: str = "en") -> str | None:
    """'3:42 PM CDT' for an ISO timestamp (naive = UTC); None if unparseable."""
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=ZoneInfo("UTC"))
    d = d.astimezone(TZ)
    return d.strftime("%-I:%M %p %Z")


def meta_of(result) -> dict:
    m = result.get("meta") if isinstance(result, dict) else None
    return m if isinstance(m, dict) else {}


def asof_phrase(result, lang: str = "en") -> str:
    """' (as of 3:42 PM CDT, provisional)' from a tool result's meta, or '' when meta/as_of is absent."""
    m = meta_of(result)
    t = local_time(m.get("as_of"), lang) if m.get("as_of") else None
    if not t:
        return ""
    parts = [ASOF.get(lang, ASOF["en"]).format(t=t)]
    if m.get("provisional"):
        parts.append(PROVISIONAL.get(lang, PROVISIONAL["en"]))
    return " (" + ", ".join(parts) + ")"


def asof_texts(results: dict) -> list[str]:
    """Local-time strings of every tool result, so numbers in 'as of 3:42 PM' count as grounded evidence."""
    return [t for r in (results or {}).values() if (t := asof_phrase(r))]


ALERT_WORDS = re.compile(r"alert|warning|watch|advisory|alerta|cảnh báo|警报|تنبيه", re.I)


def tag_live(answer: str, sources: list[str], alert_src: str, gauge_src: str, have_gauges: bool, have_alerts: bool) -> tuple[str, list[str]]:
    """The model often skips [n] on live-value sentences. A sentence stamped 'as of <time>' without a marker is
    backed by a tool: tag it with that tool's source (NWS for alerts, NOAA NWPS for gauges), adding it to sources."""
    srcs, lines = list(sources), []
    for line in answer.split("\n"):
        parts = []
        for s in SENT_RE.split(line):
            if LIVE.search(s) and not MARK.search(s):
                src = alert_src if ALERT_WORDS.search(s) and have_alerts else gauge_src if have_gauges else ""
                if src:
                    if src not in srcs:
                        srcs.append(src)
                    s = re.sub(r"([.!?。])?$", f" [{srcs.index(src) + 1}]\\1", s, count=1)
            parts.append(s)
        lines.append(" ".join(parts))
    return "\n".join(lines), srcs
