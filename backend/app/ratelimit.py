"""Tiny in-memory per-IP rate limiter + /ask length guard (pure ASGI, no deps)."""
import json
import time
from collections import defaultdict, deque

# (path prefix, max requests, window seconds)
import os
# Venue Wi-Fi puts everyone behind one public IP, so per-IP limits must be generous.
# Override with RATE_* env vars (requests per window). First matching prefix wins.
LIMITS = [
    ("/api/ask", int(os.getenv("RATE_ASK", "60")), 60),  # /ask, /ask/stream, /ask/prefetch
    ("/api/push/", int(os.getenv("RATE_PUSH", "20")), 60),
    ("/api/reports", int(os.getenv("RATE_REPORTS", "20")), 60),  # POST /reports and /reports/{id}/vote
    ("/api/plan", int(os.getenv("RATE_PLAN", "40")), 60),
    # paid upstreams (ElevenLabs, Gemini via route explanations, Twilio) and the geocoder
    ("/api/voice", int(os.getenv("RATE_VOICE", "30")), 60),  # /voice, /voice/stream, /voice/filler
    ("/api/el-agent/signed-url", int(os.getenv("RATE_EL_AGENT", "10")), 60),
    ("/api/profile", int(os.getenv("RATE_PROFILE", "30")), 60),
    ("/api/route-check", int(os.getenv("RATE_ROUTE", "30")), 60),
    ("/api/sms/", int(os.getenv("RATE_SMS", "20")), 60),
    ("/api/checkin/call", int(os.getenv("RATE_CHECKIN_CALL", "3")), 600),  # real phone calls
    ("/api/checkin/", 30, 60),
    ("/api/geocode", int(os.getenv("RATE_GEOCODE", "60")), 60),
]
# Limits apply to POST; these prefixes are also limited on GET (reads that hit a paid or rate-limited upstream).
GET_LIMITED = ("/api/voice", "/api/el-agent/", "/api/profile", "/api/geocode")
LENGTH_GUARDED = ("/api/ask", "/api/ask/stream")
MAX_QUESTION = 500
MAX_WINDOW = max(w for _, _, w in LIMITS)
SWEEP_EVERY_S = 60
_hits: dict[tuple[str, str], deque] = defaultdict(deque)
_last_sweep = 0.0


def reset() -> None:
    _hits.clear()


def _sweep(now: float) -> None:
    """Drop IPs with no hits inside the longest window so _hits does not grow forever."""
    global _last_sweep
    _last_sweep = now
    for k in [k for k, q in _hits.items() if not q or now - q[-1] > MAX_WINDOW]:
        del _hits[k]


def _allowed(ip: str, prefix: str, limit: int, window: int) -> bool:
    now = time.monotonic()
    if now - _last_sweep > SWEEP_EVERY_S:
        _sweep(now)
    q = _hits[(ip, prefix)]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


async def _json(send, status: int, body: dict, headers=()):
    data = json.dumps(body).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"), *headers]})
    await send({"type": "http.response.body", "body": data})


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path, method = scope["path"], scope["method"]
        if not (method == "POST" or (method == "GET" and path.startswith(GET_LIMITED))):
            return await self.app(scope, receive, send)
        ip = (scope.get("client") or ("unknown", 0))[0]
        for prefix, limit, window in LIMITS:
            if path.startswith(prefix):
                if not _allowed(ip, prefix, limit, window):
                    return await _json(send, 429, {"detail": "Too many requests. Please wait a minute."},
                                       [(b"retry-after", str(window).encode())])
                break
        if method == "POST" and path in LENGTH_GUARDED:
            chunks, more = [], True
            while more:
                msg = await receive()
                chunks.append(msg.get("body", b""))
                more = msg.get("more_body", False)
            body = b"".join(chunks)
            try:
                q = json.loads(body).get("question")
            except Exception:
                q = None
            if isinstance(q, str) and len(q) > MAX_QUESTION:
                return await _json(send, 422, {"detail": f"question must be at most {MAX_QUESTION} characters"})
            sent = False

            async def replay():
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()
            return await self.app(scope, replay, send)
        return await self.app(scope, receive, send)
