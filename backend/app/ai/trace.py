"""'How I answered' trace for /ask and the /ask/stream final event. Cheap, no network, no Gemini calls.
A per-request collector (contextvar holding a mutable object, so tasks spawned by gather share it) is filled by
tools.run_tool (tool name, ms, source), rag.search (retrieved chunks), telemetry (route, intents)."""
import contextvars
import time

_cur: contextvars.ContextVar["Collector | None"] = contextvars.ContextVar("ask_trace", default=None)


class Collector:
    def __init__(self):
        self.t0 = time.perf_counter()
        self.intents: list[str] = []
        self.route = "template"
        self.tools: list[dict] = []
        self.retrieved: list[dict] = []
        self.llm_ms = 0
        self.cache_hit = "none"


def begin() -> Collector:
    c = Collector()
    _cur.set(c)
    return c


def current() -> Collector | None:
    return _cur.get()


def add_tool(name: str, ms: float, source: str | None) -> None:
    c = _cur.get()
    if c is not None:
        c.tools.append({"name": name, "ms": int(ms), "source": source})


def add_retrieved(chunks) -> None:
    c = _cur.get()
    if c is not None and chunks and not c.retrieved:
        c.retrieved = [{"title": h.get("title", ""), "source": h.get("source", ""),
                        **({"score": round(float(h["score"]), 3)} if h.get("score") is not None else {})}
                       for h in chunks[:3]]


def set_route(route: str) -> None:
    c = _cur.get()
    if c is not None:
        c.route = ROUTES.get(route) or ("prefetch" if route.startswith("llm") else "template")


ROUTES = {"cache": "cache", "graph": "graph", "prefetch": "prefetch"}


def build(c: Collector | None, generated_by: str, ctx=None) -> dict:
    """Final trace dict; always the full shape (empty lists when a step did not run)."""
    c = c or Collector()
    total = int((time.perf_counter() - c.t0) * 1000)
    retrieved, seen = [], set()
    for h in (ctx or []):
        k = (h.get("title", ""), h.get("source", ""))
        if k not in seen and len(retrieved) < 3:
            seen.add(k)
            retrieved.append({"title": k[0], "source": k[1]})
    retrieved = retrieved or c.retrieved
    gem = generated_by == "gemini"
    return {
        "intent": ", ".join(c.intents) if c.intents else "general",
        "route": c.route,
        "cache_hit": c.cache_hit,
        "retrieved": retrieved,
        "tools": c.tools,
        "answer": {"by": "gemini" if gem else "template",
                   "ms": c.llm_ms if gem else max(0, total - max([t["ms"] for t in c.tools] or [0]))},
        "total_ms": total,
    }
