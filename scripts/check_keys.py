"""Check each configured API key with one cheap call. Never prints key values.

Run: cd backend && uv run python ../scripts/check_keys.py
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:  # missing dotenv or file is fine
    pass


def report(name: str, status: str, reason: str = "") -> None:
    print(f"[{status:<7}] {name}" + (f": {reason}" if reason else ""))


def scrub(msg: str, *secrets: str) -> str:
    for s in secrets:
        if s:
            msg = msg.replace(s, "***")
    return msg.replace("\n", " ")[:200]


def check_gemini() -> None:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return report("GEMINI_API_KEY", "MISSING", "not set; app uses template/BM25 fallbacks")
    model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    embed = os.getenv("GEMINI_EMBED_MODEL") or "gemini-embedding-001"
    try:
        from google import genai

        client = genai.Client(api_key=key)
    except Exception as e:
        return report("GEMINI_API_KEY", "FAIL", scrub(f"client init: {e}", key))
    try:
        r = client.models.generate_content(model=model, contents="Reply with the word ok.")
        report("GEMINI generate", "OK", f"{model} replied ({len(r.text or '')} chars)")
    except Exception as e:
        msg = scrub(str(e), key)
        report("GEMINI generate", "FAIL", f"{model}: {msg}")
        if "404" in msg or "not found" in msg.lower():
            try:
                names = [
                    m.name for m in client.models.list() if "flash" in (m.name or "").lower()
                ]
                print("          available flash models: " + ", ".join(names[:15]))
            except Exception as e2:
                print("          could not list models: " + scrub(str(e2), key))
    try:
        r = client.models.embed_content(model=embed, contents="flood")
        dim = len(r.embeddings[0].values)
        report("GEMINI embed", "OK", f"{embed} dim={dim}")
    except Exception as e:
        report("GEMINI embed", "FAIL", f"{embed}: {scrub(str(e), key)}")


def check_elevenlabs() -> None:
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key:
        return report("ELEVENLABS_API_KEY", "MISSING", "not set; app uses browser speechSynthesis")
    try:
        r = httpx.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": key},
            timeout=10,
        )
        if r.status_code == 200:
            d = r.json()
            left = d.get("character_limit", 0) - d.get("character_count", 0)
            report("ELEVENLABS", "OK", f"{left} characters remaining (tier {d.get('tier')})")
        elif r.status_code == 401 and "missing_permissions" in r.text:
            # a TTS-only key can't read the subscription; that's fine for the app
            report("ELEVENLABS", "WARN", "key can't read usage (no user_read permission); TTS may still work - test POST /api/voice")
        else:
            report("ELEVENLABS", "FAIL", f"HTTP {r.status_code}: {scrub(r.text, key)[:120]}")
    except Exception as e:
        report("ELEVENLABS", "FAIL", scrub(str(e), key))


def check_backboard() -> None:
    key = os.getenv("BACKBOARD_API_KEY", "")
    if not key:
        return report("BACKBOARD_API_KEY", "MISSING", "not set; app uses local DB memory")
    base = os.getenv("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
    try:
        r = httpx.get(f"{base}/assistants", headers={"X-API-Key": key}, timeout=10)
        if r.status_code == 200:
            report("BACKBOARD", "OK", "authenticated GET /assistants")
        else:
            report("BACKBOARD", "FAIL", f"HTTP {r.status_code}: {scrub(r.text, key)[:120]}")
    except Exception as e:
        report("BACKBOARD", "FAIL", scrub(str(e), key))


def check_db() -> None:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return report("DATABASE_URL", "MISSING", "not set; app uses local SQLite")
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(url, connect_args={"connect_timeout": 10} if "postgres" in url else {})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            if engine.dialect.name != "postgresql":
                return report("DATABASE_URL", "OK", f"connected ({engine.dialect.name}); no extensions")
            avail = {
                r[0]
                for r in conn.execute(
                    text("SELECT name FROM pg_available_extensions WHERE name IN ('timescaledb','vector')")
                )
            }
        ext = ", ".join(f"{n}={'available' if n in avail else 'NOT available'}" for n in ("timescaledb", "vector"))
        report("DATABASE_URL", "OK", f"connected; {ext}")
    except Exception as e:
        report("DATABASE_URL", "FAIL", scrub(str(e), url))


def check_vapid() -> None:
    for k in ("VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY"):
        if os.getenv(k):
            report(k, "OK", "present")
        else:
            report(k, "MISSING", "not set; auto-generated and persisted at startup")


if __name__ == "__main__":
    for fn in (check_gemini, check_elevenlabs, check_backboard, check_db, check_vapid):
        try:
            fn()
        except Exception as e:  # never crash
            report(fn.__name__, "FAIL", scrub(str(e)))
