"""Shared paths and env helpers for the AI module."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]  # repo root
BACKEND = ROOT / "backend"
load_dotenv(ROOT / ".env")


def gemini_keys() -> list[str]:
    """GEMINI_API_KEYS (comma-separated) plus GEMINI_API_KEY, de-duplicated, order kept. Never log these."""
    raw = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")]
    raw.append(os.getenv("GEMINI_API_KEY", "").strip())
    return list(dict.fromkeys(k for k in raw if k))


def gemini_key() -> str:
    ks = gemini_keys()
    return ks[0] if ks else ""


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def embed_model() -> str:
    return os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")


def database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{BACKEND / 'floodready.db'}"


def sqlalchemy_url() -> str:
    """database_url() normalized to the psycopg3 driver (Tiger Data gives postgres://...)."""
    u = database_url()
    for pre in ("postgres://", "postgresql://"):
        if u.startswith(pre):
            return "postgresql+psycopg://" + u[len(pre):]
    return u


# --- quota-aware rotation -------------------------------------------------------------------------------------
# Free-tier quotas are per (project/key, model). A 429/404 marks that pair exhausted for its retry window
# (persisted in backend/.cache/quota.json so a reload keeps it) and the caller moves to the next pair.
import hashlib
import json
import re
import threading
import time

LITE_MODELS = ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-2.5-flash-lite")
FALLBACK_MODELS = LITE_MODELS  # kept for imports
LIVE_FALLBACKS = ("gemini-3.8-live", "gemini-3.1-flash-live-preview", "gemini-2.5-flash-native-audio-latest")
DEFAULT_WINDOW_S = 3600
QUOTA_FILE = BACKEND / ".cache" / "quota.json"
_lock = threading.Lock()
_state: dict[str, float] | None = None  # "<keyid>|<model>" -> unix time until which the pair is skipped
class _Last:
    v = ""

    def get(self) -> str:
        return self.v

    def set(self, m: str) -> None:
        self.v = m


last_model = _Last()  # last model that answered (process-wide; plain attribute so it survives task contexts)


def _kid(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()[:8]


def _load() -> dict[str, float]:
    global _state
    if _state is None:
        try:
            _state = {k: float(v) for k, v in json.loads(QUOTA_FILE.read_text()).items()}
        except Exception:  # noqa: BLE001
            _state = {}
    return _state


def _save() -> None:
    try:
        QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
        QUOTA_FILE.write_text(json.dumps(_state or {}))
    except Exception:  # noqa: BLE001
        pass


def reset_quota() -> None:
    global _state
    with _lock:
        _state = {}


def _norm(model: str) -> str:
    return model.removeprefix("models/")


def is_exhausted(key: str, model: str) -> bool:
    now = time.time()
    with _lock:
        st = _load()
        until = st.get(f"{_kid(key)}|{_norm(model)}", 0)
        if until and until <= now:
            st.pop(f"{_kid(key)}|{_norm(model)}", None)
            return False
        return until > now


def retry_delay_s(e: Exception) -> float:
    """Seconds from a 'retryDelay': '34s' / 'Please retry in 34.5s' in the error text, else the 1 h default."""
    s = str(e)
    m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", s) or re.search(r"retry in (\d+(?:\.\d+)?)s", s)
    return max(float(m.group(1)), 1.0) if m else float(DEFAULT_WINDOW_S)


def mark_exhausted(key: str, model: str, e: Exception | None = None) -> None:
    secs = retry_delay_s(e) if e is not None else DEFAULT_WINDOW_S
    with _lock:
        _load()[f"{_kid(key)}|{_norm(model)}"] = time.time() + secs
        _save()


def mark_dead(model: str, key: str = "") -> None:
    """404: the model is unavailable (for this key, or for all keys when none is given)."""
    for k in ([key] if key else gemini_keys()):
        mark_exhausted(k, model)


def is_quota_error(e: Exception) -> bool:
    s = f"{type(e).__name__} {e}".lower()
    return "429" in s or "resource_exhausted" in s or "quota" in s or "rate limit" in s


def is_model_not_found(e: Exception) -> bool:
    s = f"{type(e).__name__} {e}".lower()
    return ("not found" in s or "not_found" in s or "notfound" in s or "404" in s
            or "is not supported" in s or "unknown model" in s)


def should_rotate(e: Exception) -> bool:
    return is_quota_error(e) or is_model_not_found(e)


def _ordered(first: list[str], rest) -> list[str]:
    return [_norm(m) for m in dict.fromkeys([m for m in [*first, *rest] if m])]


def chat_models() -> list[str]:
    return _ordered([os.getenv("GEMINI_CHAT_MODEL", "").strip() or os.getenv("GEMINI_VOICE_MODEL", "").strip()], LITE_MODELS)


def voice_models() -> list[str]:
    return _ordered([os.getenv("GEMINI_VOICE_MODEL", "").strip()], LITE_MODELS)


def complex_models() -> list[str]:
    return _ordered([gemini_model()], LITE_MODELS)


def live_model_list() -> list[str]:
    return _ordered([os.getenv("GEMINI_LIVE_MODEL", "").strip()], LIVE_FALLBACKS)


def gemini_models() -> list[str]:
    """Configured complex model first, then the lite fallbacks."""
    return complex_models()


def pairs(models) -> list[tuple[str, str]]:
    """(key, model) pairs not currently exhausted, models-major (best model first, every key before the next
    model). Never empty when keys exist: if everything is exhausted, the full list is returned (best effort)."""
    keys = gemini_keys()
    allp = [(k, _norm(m)) for m in dict.fromkeys(models) for k in keys]
    return [p for p in allp if not is_exhausted(*p)] or allp


def live(models) -> list[str]:
    """Models with at least one non-exhausted key; never empty."""
    ms = list(dict.fromkeys(_norm(m) for m in models))
    keys = gemini_keys()
    return [m for m in ms if not keys or any(not is_exhausted(k, m) for k in keys)] or ms


def quota_status() -> dict:
    """For /api/status: no keys, only counts."""
    ms = list(dict.fromkeys([*chat_models(), *complex_models(), *voice_models()]))
    keys = gemini_keys()
    ex = [m for m in ms if keys and all(is_exhausted(k, m) for k in keys)]
    active = next((m for m in chat_models() if m not in ex), "")
    return {"active_model": active, "last_model": last_model.get() or None, "keys": len(keys),
            "models_total": len(ms), "models_exhausted": len(ex), "exhausted": ex}
