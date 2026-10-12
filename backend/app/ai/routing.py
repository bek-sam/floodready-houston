"""Request routing: deterministic (no-LLM) answers for fixed-answer intents, tool selection,
compact tool JSON for prompts, and lite-vs-strong model choice."""
import json
import re

from . import citations, decide, graph
from .grounding import sanitize_untrusted, wrap_untrusted

NWS_SRC = "https://www.weather.gov/documentation/services-web-api"
LOC_TOOLS = {"get_risk", "get_alerts", "get_civic", "get_shelters", "get_flood_history", "get_medical", "check_route",
             "get_reservoir_pool", "get_rain", "get_nri", "get_parking"}
DANGER = {"emergency", "street_flood"}

WAIT_RE = re.compile(r"wait|how long|when (does|will|do)[^?]*(start|begin|effective|kick in|covered)|take effect|30[- ]?day|"
                     r"espera|cu[aá]ndo (empieza|comienza)|cu[aá]nto tarda|thời gian chờ|bao lâu|等待|多久|生效|انتظار|متى", re.I)
ALERT_RE = re.compile(r"\b(alerts?|warnings?|watch(es)?|advisor(y|ies))\b|alertas?|advertencias?|avisos?|cảnh báo|警报|预警|警告|تنبيه|تحذير", re.I)
SIGNUP_RE = re.compile(r"sign ?up|subscribe|register|get (the )?alerts|how (do|can) i (get|receive)|inscrib|registr|suscrib|đăng ký|订阅|注册|اشتراك|تسجيل", re.I)
DATE_RE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")

L = {  # deterministic templates (short, sourced)
    "countdown": {
        "en": "Flood insurance from the NFIP usually has a 30-day waiting period{c} (a few exceptions exist, e.g. buying with a mortgage; ask your agent). If you buy a policy today ({p}), coverage generally starts {e}; until then you have no flood coverage. {season} Buy before a storm is forecast.",
        "es": "El seguro de inundación del NFIP normalmente tiene un período de espera de 30 días{c} (hay algunas excepciones, p. ej. al comprar con una hipoteca; pregunte a su agente). Si compra una póliza hoy ({p}), la cobertura generalmente empieza el {e}; hasta entonces no tiene cobertura. {season} Compre antes de que se pronostique una tormenta.",
        "vi": "Bảo hiểm lũ NFIP thường có thời gian chờ 30 ngày{c} (có một vài ngoại lệ, ví dụ khi mua cùng khoản vay thế chấp; hãy hỏi đại lý của bạn). Nếu bạn mua hôm nay ({p}), bảo hiểm thường bắt đầu từ {e}; trước đó bạn không được bảo hiểm lũ. {season} Hãy mua trước khi có dự báo bão.",
        "zh": "NFIP洪水保险通常有30天的等待期{c}（有少数例外，例如随房贷一起购买；请咨询您的保险代理人）。如果您今天（{p}）购买，保障一般从{e}开始；在此之前您没有洪水保障。{season}请在风暴预报之前购买。",
        "ar": "عادةً ما يكون لتأمين الفيضانات من NFIP فترة انتظار مدتها 30 يومًا{c} (توجد بعض الاستثناءات، مثل الشراء مع قرض عقاري؛ اسأل وكيلك). إذا اشتريت وثيقة اليوم ({p})، تبدأ التغطية عادةً في {e}؛ وقبل ذلك لا توجد لديك تغطية للفيضانات. {season} اشترِ قبل التنبؤ بالعاصفة.",
    },
    "season_in": {"en": "That is before hurricane season ends ({d}).", "es": "Eso es antes de que termine la temporada de huracanes ({d}).",
                  "vi": "Ngày đó trước khi mùa bão kết thúc ({d}).", "zh": "这在飓风季结束（{d}）之前。", "ar": "وذلك قبل نهاية موسم الأعاصير ({d})."},
    "season_out": {"en": "That is after hurricane season ends ({d}).", "es": "Eso es después de que termine la temporada de huracanes ({d}).",
                   "vi": "Ngày đó sau khi mùa bão kết thúc ({d}).", "zh": "这在飓风季结束（{d}）之后。", "ar": "وذلك بعد نهاية موسم الأعاصير ({d})."},
    "alerts_none": {"en": "There are no active flood-related National Weather Service alerts for your location right now{c}.",
                    "es": "No hay alertas activas del Servicio Meteorológico Nacional relacionadas con inundaciones para su ubicación en este momento{c}.",
                    "vi": "Hiện không có cảnh báo lũ nào đang hiệu lực của Cơ quan Thời tiết Quốc gia cho vị trí của bạn{c}.",
                    "zh": "您所在位置目前没有与洪水相关的美国国家气象局有效警报{c}。",
                    "ar": "لا توجد حاليًا تنبيهات نشطة من هيئة الأرصاد الجوية الوطنية متعلقة بالفيضانات لموقعك{c}."},
    "alerts_some": {"en": "Active National Weather Service alerts for your location{c}:", "es": "Alertas activas del Servicio Meteorológico Nacional para su ubicación{c}:",
                    "vi": "Cảnh báo đang hiệu lực của Cơ quan Thời tiết Quốc gia cho vị trí của bạn{c}:", "zh": "您所在位置的美国国家气象局有效警报{c}：",
                    "ar": "تنبيهات هيئة الأرصاد الجوية الوطنية النشطة لموقعك{c}:"},
    "alerts_err": {"en": "I could not load live National Weather Service alerts right now{c}; check weather.gov or local news.",
                   "es": "No pude cargar las alertas del Servicio Meteorológico Nacional ahora{c}; consulte weather.gov o las noticias locales.",
                   "vi": "Tôi không tải được cảnh báo của Cơ quan Thời tiết Quốc gia lúc này{c}; hãy xem weather.gov hoặc tin tức địa phương.",
                   "zh": "目前无法加载美国国家气象局的实时警报{c}；请查看 weather.gov 或本地新闻。",
                   "ar": "تعذر تحميل تنبيهات هيئة الأرصاد الجوية الوطنية الآن{c}؛ راجع weather.gov أو الأخبار المحلية."},
    "alerts_tip": {"en": "Conditions change fast: keep phone emergency alerts on.", "es": "Las condiciones cambian rápido: mantenga activas las alertas de emergencia del teléfono.",
                   "vi": "Tình hình thay đổi nhanh: hãy bật cảnh báo khẩn cấp trên điện thoại.", "zh": "情况变化很快：请保持手机紧急警报开启。",
                   "ar": "الظروف تتغير بسرعة: أبقِ تنبيهات الطوارئ في هاتفك مفعّلة."},
    "zip": {"en": "ZIP {z} has {t} NFIP flood insurance claims on record, {s} of them since 2017{c}.{pol}",
            "es": "El código postal {z} tiene {t} reclamos al seguro de inundación NFIP registrados, {s} desde 2017{c}.{pol}",
            "vi": "Mã ZIP {z} có {t} yêu cầu bồi thường bảo hiểm lũ NFIP được ghi nhận, {s} trong số đó từ năm 2017{c}.{pol}",
            "zh": "邮编{z}共有{t}笔NFIP洪水保险理赔记录，其中{s}笔发生在2017年以后{c}。{pol}",
            "ar": "يوجد في الرمز البريدي {z} عدد {t} من مطالبات تأمين الفيضانات NFIP المسجلة، منها {s} منذ 2017{c}.{pol}"},
    "zip_pol": {"en": " {n} flood policies are in force there.", "es": " Hay {n} pólizas de inundación vigentes allí.",
                "vi": " Hiện có {n} hợp đồng bảo hiểm lũ đang hiệu lực ở đó.", "zh": "该地区目前有{n}份有效的洪水保单。",
                "ar": " توجد هناك {n} وثيقة تأمين فيضانات سارية."},
    "zip_peak": {"en": "The most claims were in {y} ({n}).", "es": "El año con más reclamos fue {y} ({n}).",
                 "vi": "Năm có nhiều yêu cầu nhất là {y} ({n}).", "zh": "理赔最多的年份是{y}年（{n}笔）。",
                 "ar": "كان أكبر عدد من المطالبات في {y} ({n})."},
    "zip_note": {"en": "Claims show past flooding in the ZIP, not your exact street; few claims does not mean safe.",
                 "es": "Los reclamos muestran inundaciones pasadas en el código postal, no en su calle; pocos reclamos no significa que sea seguro.",
                 "vi": "Số yêu cầu cho thấy lũ trong quá khứ ở mã ZIP, không phải đúng con đường của bạn; ít yêu cầu không có nghĩa là an toàn.",
                 "zh": "理赔反映的是该邮编过去的水灾，而不是您所在的具体街道；理赔少并不代表安全。",
                 "ar": "تُظهر المطالبات الفيضانات السابقة في الرمز البريدي وليس شارعك بالتحديد؛ قلة المطالبات لا تعني الأمان."},
}


def _l(key: str, lang: str) -> str:
    return L[key].get(lang, L[key]["en"])


def _disc(lang: str) -> str:
    return graph.DISCLAIMER.get(lang, graph.DISCLAIMER["en"]) if lang != "en" else "Not official guidance. In danger, call 911."


def kind(s: dict) -> str | None:
    """Which deterministic route applies, if any. Danger and multi-intent questions always go to the model."""
    it = set(s.get("intents") or [])
    q = graph._qtext(s)
    has_loc = s.get("lat") is not None and s.get("lon") is not None
    if it & DANGER:
        return None
    if it == {"shelter"}:
        return "shelter"
    if it == {"insurance"} and WAIT_RE.search(q):
        return "countdown"
    if it <= {"zip_insurance", "insurance"} and "zip_insurance" in it and graph.zip_in_text(q):
        return "zip_claims"
    if has_loc and it <= {"general", "risk"} and ALERT_RE.search(q) and not SIGNUP_RE.search(q):
        return "alerts"
    return None


async def deterministic(s: dict, run_tool) -> dict | None:
    """Answer from service data with templates, no LLM. Returns {answer, sources, tools_used, route, evidence} or None."""
    seen: dict = {}

    async def tool(name, args):
        seen[name] = r = await run_tool(name, args)
        return r
    out = await _deterministic(s, tool)
    if out:
        out["evidence"] = [f"{n}: {tool_json(n, r)}" for n, r in seen.items()]
        if out["route"] == "det_countdown":
            from . import rag
            c = rag.card_chunk("insurance-30-day-and-gap.md", "fact", "forecast")
            if c:
                out["evidence"].append(f"[{c['source']}] {c['text']}")
        if out["route"] == "det_shelter":
            out["evidence"].append(graph.SHELTER_NOTE(s.get("lang", "en")))
    return out


async def _deterministic(s: dict, run_tool) -> dict | None:
    k = kind(s)
    if not k:
        return None
    lang = s.get("lang", "en")
    q = graph._qtext(s)
    here = {"lat": s.get("lat"), "lon": s.get("lon")}
    cite = graph.Cites()
    if k == "shelter":
        used, res = [], {}
        if here["lat"] is not None and here["lon"] is not None:
            res["get_shelters"] = await run_tool("get_shelters", {**here, "pet_friendly": bool(re.search(r"\bpets?\b|dog|cat|mascota", q.lower()))})
            used.append("get_shelters")
        out = graph.answer_with_citations({**s, "context": [], "tool_results": res, "generated_by": "template"})
        return {"answer": out["answer"], "sources": out["sources"], "tools_used": used, "route": "det_shelter"}
    if k == "countdown":
        m = DATE_RE.search(q)
        ins = await run_tool("insurance_countdown", {"purchase_date": m.group(1) if m else ""})
        if not isinstance(ins, dict) or "error" in ins or not ins.get("effective_date"):
            return None
        season = _l("season_in" if ins.get("covered_before_season_end") else "season_out", lang).format(d=ins.get("season_end", ""))
        body = _l("countdown", lang).format(c=cite(str(ins.get("source", ""))), p=ins.get("purchase_date", ""), e=ins["effective_date"],
                                           season=season if ins.get("season_end") else "")
        return {"answer": re.sub(r"\s+\n|  +", " ", body).strip() + "\n" + _disc(lang), "sources": cite.urls,
                "tools_used": ["insurance_countdown"], "route": "det_countdown"}
    if k == "zip_claims":
        z = graph.zip_in_text(q)
        zi = await run_tool("get_zip_insurance", {"zip": z})
        cl = (zi or {}).get("claims") or {} if isinstance(zi, dict) else {}
        if not isinstance(zi, dict) or "error" in zi or zi.get("warnings") or not cl.get("total"):
            return None  # unknown data: let the model / template explain
        pol = zi.get("policies_in_force")
        lines = [_l("zip", lang).format(z=z, t=cl["total"], s=cl.get("since_2017", "?"), c=cite(str(zi.get("source", ""))),
                                        pol=_l("zip_pol", lang).format(n=pol) if pol is not None else "")]
        by = [y for y in cl.get("by_year") or [] if isinstance(y, dict) and y.get("count")]
        if by:
            top = max(by, key=lambda y: y["count"])
            lines[0] += " " + _l("zip_peak", lang).format(y=top["year"], n=top["count"])
        lines += [_l("zip_note", lang), _disc(lang)]
        return {"answer": "\n".join(lines), "sources": cite.urls, "tools_used": ["get_zip_insurance"], "route": "det_zip"}
    if k == "alerts":
        al = await run_tool("get_alerts", here)
        c = cite(NWS_SRC)
        ca = citations.asof_phrase(al, lang) + c if isinstance(al, dict) else c  # "(as of 3:42 PM CDT) [1]"
        if not isinstance(al, dict) or "error" in al or al.get("warnings"):
            lines = [_l("alerts_err", lang).format(c=c)]
        else:
            items = [a for a in al.get("alerts") or [] if any(w in str(a.get("event", "")).lower() for w in graph.FLOOD_EVENTS)]
            if not items:
                lines = [_l("alerts_none", lang).format(c=ca)]
            else:
                lines = [_l("alerts_some", lang).format(c=ca)]
                lines += [f"- {sanitize_untrusted(a.get('headline') or a.get('event'), 220)}" for a in items[:3]]
        lines += [_l("alerts_tip", lang), _disc(lang)]
        return {"answer": "\n".join(lines), "sources": cite.urls, "tools_used": ["get_alerts"], "route": "det_alerts"}
    return None


# ---------- tool selection for the single-call path ----------
def knowledge_only(s: dict) -> bool:
    from . import cache
    it = set(s.get("intents") or [])
    return bool(it) and it <= cache.KNOWLEDGE_INTENTS and not cache.PERSONAL.search(s.get("question", ""))


def select_tools(s: dict) -> list[tuple[str, dict]]:
    """Intent-matched tools (graph._fallback_tools), plus risk alongside flood history; none for knowledge-only questions."""
    calls = graph._fallback_tools(s)
    names = [n for n, _ in calls]
    if "get_flood_history" in names and "get_risk" not in names and s.get("lat") is not None:
        calls.append(("get_risk", {"lat": s["lat"], "lon": s["lon"]}))
    if ALERT_RE.search(graph._qtext(s)) and "get_alerts" not in names and s.get("lat") is not None:
        calls.append(("get_alerts", {"lat": s["lat"], "lon": s["lon"]}))
    if knowledge_only(s):
        calls = [c for c in calls if c[0] not in LOC_TOOLS]
    elif s.get("lat") is not None and s.get("lon") is not None:  # Jev may ADD location tools, never remove any
        calls += [(n, _loc_args(n, s)) for n in decide.extra_tools(s.get("jev"), [n for n, _ in calls])]
    return calls


def _loc_args(name: str, s: dict) -> dict:
    """Arguments for a location tool, same as graph._fallback_tools builds them."""
    here, q = {"lat": s["lat"], "lon": s["lon"]}, graph._qtext(s).lower()
    if name == "get_shelters":
        return {**here, "pet_friendly": bool(re.search(r"\bpets?\b|dog|cat", q))}
    if name == "get_flood_history":
        return {**here, "zip": graph.zip_in_text(q)}
    if name == "get_medical":
        return {**here, "kind": "dialysis", "limit": 3}
    return here


# ---------- model choice ----------
def complex_question(s: dict) -> bool:
    """Jev complexity score when confident, else: two or more intents or a long question."""
    jev = decide.is_complex(s.get("jev"))
    if jev is not None:
        return jev
    it = set(s.get("intents") or []) - {"general"}
    return len(it) >= 2 or len(s.get("question", "")) > 160


# ---------- compact tool JSON ----------
MAX_TOOL_CHARS = 800


def _pick(d, keys):
    return {k: d[k] for k in keys if isinstance(d, dict) and d.get(k) not in (None, "", [], {})}


def compact(name: str, r) -> dict | list:
    """Only the fields the answer needs; user-generated text is sanitized and marked untrusted."""
    out = _compact(name, r)
    if name in ("get_risk", "get_alerts") and isinstance(out, dict):  # freshness: local time the model can quote
        ph = citations.asof_phrase(r).strip(" ()")
        if ph:
            out = {**out, "as_of": ph}
    return out


def _compact(name: str, r) -> dict | list:
    if not isinstance(r, dict):
        return r[:4] if isinstance(r, list) else r
    if name == "get_risk":
        g = [_pick(x, ["name", "status", "stage_ft"]) for x in (r.get("nearest_gauges") or [])[:2]]
        return {**_pick(r, ["fema_zone", "zone_subtype", "sfha", "elevation_ft", "low_ground", "jurisdiction", "reservoir_area"]),
                "harvey": _pick(r.get("harvey") or {}, ["flooded", "source"]), "nearest_gauges": g,
                "facts": [_pick(f, ["text", "source"]) for f in (r.get("facts") or [])[:2]]}
    if name == "get_flood_history":
        ev = [{"name": e.get("name"), **_pick(e.get("nearest_gauge") or {}, ["name", "distance_mi", "peak_ft", "peak_category"])}
              for e in (r.get("events") or [])[:4]]
        return {"harvey": _pick(r.get("harvey") or {}, ["flooded", "source"]), "events": ev, "zip": r.get("zip")}
    if name == "get_zip_insurance":
        cl = r.get("claims") or {}
        by = sorted([y for y in cl.get("by_year") or [] if isinstance(y, dict)], key=lambda y: -(y.get("count") or 0))[:3]
        return {**_pick(r, ["zip", "policies_in_force", "source", "note"]),
                "claims": {**_pick(cl, ["total", "since_2017"]), "top_years": by},
                "premiums": _pick(r.get("premiums") or {}, ["median_annual", "p25", "p75"])}
    if name == "get_alerts":
        return {"alerts": [_pick(a, ["event", "severity", "headline", "expires"]) for a in (r.get("alerts") or [])[:3]],
                **_pick(r, ["warnings"])}
    if name == "get_shelters":
        return {**_pick(r, ["historical", "any_open", "data_as_of", "note", "source"]),
                "shelters": [_pick(x, ["name", "distance_mi", "pet_friendly", "status_2017"]) for x in (r.get("shelters") or [])[:3]]}
    if name == "get_medical":
        return {**_pick(r, ["note", "source"]),
                "facilities": [_pick(x, ["name", "phone", "distance_mi", "fema_zone", "sfha", "harvey_flooded"])
                               for x in (r.get("facilities") or [])[:3]]}
    if name == "get_reservoir_pool":
        return {**_pick(r, ["available", "relevant", "ground_elevation_ft", "pool_below_ground_ft", "harvey_above_ground_ft",
                            "message", "warnings", "source"]),
                "pool": _pick(r.get("pool") or {}, ["stage_ft", "status", "observed_at", "action_ft", "minor_ft", "harvey_crest_ft"])}
    if name == "get_declarations":
        return {**_pick(r, ["available", "active_ia", "warnings", "note", "source"]),
                "latest": _pick(r.get("latest") or {}, ["title", "incident_type", "declaration_date", "ia_program", "url"]),
                "recent": [_pick(x, ["title", "declaration_date", "ia_program"]) for x in (r.get("recent") or [])[1:4]]}
    if name == "get_rain":
        return {**_pick(r, ["available", "total_inches", "wettest_window", "max_pop_pct", "warnings", "source"]),
                "past": _pick(r.get("past") or {}, ["available", "last24_in", "last72_in", "peak_hour"]),
                "action": (r.get("action") or {}).get("text")}
    if name == "get_nri":
        return _pick(r, ["available", "inland_flood", "expected_loss_rating", "resilience", "social_vulnerability",
                         "overall_risk", "note", "warnings", "source"])
    if name == "get_power_dependent":
        return {**_pick(r, ["zip", "available", "medicare_benes", "power_dependent_devices", "oxygen", "dialysis",
                            "note", "warnings", "source"]),
                "puc": _pick(r.get("puc") or {}, ["url"])}
    if name == "get_parking":
        return {**_pick(r, ["verdict", "headline", "fema_zone", "harvey_flooded", "elevation_ft", "warnings", "source"]),
                "reasons": [x.get("text") for x in (r.get("reasons") or [])[:3] if isinstance(x, dict)],
                "crossings": [_pick(x, ["name", "distance_m"]) for x in (r.get("crossings_within_300m") or [])[:2]],
                "alerts": [a.get("event") for a in (r.get("active_flood_alerts") or [])[:2] if isinstance(a, dict)],
                "higher_ground": r.get("higher_ground")}
    if name == "get_civic":
        b = r.get("bond") or {}
        return {"bond_facts": [_pick(f, ["text", "source"]) for f in (b.get("facts") or [])[:2]],
                "reservoir": _pick(r.get("reservoir") or {}, ["in_area"]),
                "responsibility": [_pick(x, ["issue", "agency", "contact"]) for x in (r.get("responsibility") or [])[:3]]}
    if name == "check_route":
        hz = []
        for h in (r.get("hazards") or [])[:4]:
            item = _pick(h, ["name", "kind"])
            reason = h.get("reason", "")
            item["reason"] = wrap_untrusted(reason) if h.get("kind") == "report" else sanitize_untrusted(reason, 160)
            hz.append(item)
        return {**_pick(r, ["verdict", "message"]), "hazards": hz}
    return r


def tool_json(name: str, r) -> str:
    s = json.dumps(compact(name, r), default=str, ensure_ascii=False, separators=(",", ":"))
    return s if len(s) <= MAX_TOOL_CHARS else s[:MAX_TOOL_CHARS - 1] + "…"
