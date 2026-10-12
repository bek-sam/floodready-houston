import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mkdtemp() + "/t.db"
# Never hit real paid APIs from tests: blank the keys before app imports load .env
# (load_dotenv does not override variables that are already set). Keyed-path tests
# set fake keys themselves via monkeypatch.
for _k in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "BACKBOARD_API_KEY", "TYPESAFE_API_KEY"):
    os.environ[_k] = ""

import pytest


@pytest.fixture(autouse=True)
def _isolated_quota(tmp_path, monkeypatch):
    """Keyed-path tests mark fake keys exhausted; keep that state out of backend/.cache and out of other tests."""
    from app.ai import config
    monkeypatch.setattr(config, "QUOTA_FILE", tmp_path / "quota.json")
    config.reset_quota()
    yield
    config.reset_quota()
