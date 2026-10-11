import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mkdtemp() + "/t.db"
# Never hit real paid APIs from tests: blank the keys before app imports load .env
# (load_dotenv does not override variables that are already set). Keyed-path tests
# set fake keys themselves via monkeypatch.
for _k in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "BACKBOARD_API_KEY"):
    os.environ[_k] = ""
