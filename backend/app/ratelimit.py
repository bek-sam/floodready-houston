"""Tiny in-memory per-IP rate limiter + /ask length guard (pure ASGI, no deps)."""
import json
import time
from collections import defaultdict, deque

# (path prefix, max requests, window seconds)
import os
# Venue Wi-Fi puts everyone behind one public IP, so per-IP limits must be generous.
# Override with RATE_ASK / RATE_PUSH / RATE_PLAN (requests per minute).
LIMITS = [
    ("/api/ask", int(os.getenv("RATE_ASK", "60")), 60),
    ("/api/push/", int(os.getenv("RATE_PUSH", "20")), 60),
    ("/api/plan", int(os.getenv("RATE_PLAN", "40")), 60),
]
MAX_QUESTION = 500
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def reset() -> None:
    _hits.clear()


def _allowed(ip: str, prefix: str, limit: int, window: int) -> bool:
    now = time.monotonic()
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
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        path = scope["path"]
        ip = (scope.get("client") or ("unknown", 0))[0]
        for prefix, limit, window in LIMITS:
            if path.startswith(prefix):
                if not _allowed(ip, prefix, limit, window):
                    return await _json(send, 429, {"detail": "Too many requests. Please wait a minute."},
                                       [(b"retry-after", str(window).encode())])
                break
        if path == "/api/ask":
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
