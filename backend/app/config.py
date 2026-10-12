"""Settings from env (repo-root .env is loaded in main.py)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
USER_AGENT = "FloodReadyHouston/0.1 (hackathon)"
HTTP_TIMEOUT = 8.0


def allowed_origins() -> list[str]:
    """Browser origins allowed by CORS and by the /api/live WebSocket origin check (ALLOWED_ORIGINS, comma-separated)."""
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()] or [
        "http://localhost:5173", "http://127.0.0.1:5173"]


def database_url() -> str:
    return os.getenv("DATABASE_URL") or f"sqlite:///{ROOT / 'backend' / 'floodready.db'}"


def key_flags() -> dict:
    return {
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
        "backboard": bool(os.getenv("BACKBOARD_API_KEY")),
        "db": bool(os.getenv("DATABASE_URL")),
    }
