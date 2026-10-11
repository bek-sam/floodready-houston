"""Tiny JSON-file cache in backend/.cache/ (survives restarts; used for geocode, routes, ArcGIS snapshots)."""
import json
import logging
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"
log = logging.getLogger("diskcache")
_mem: dict = {}


def _path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"


def load(name: str) -> dict:
    if name not in _mem:
        try:
            _mem[name] = json.loads(_path(name).read_text())
        except Exception:
            _mem[name] = {}
    return _mem[name]


def save(name: str) -> None:
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        _path(name).write_text(json.dumps(_mem.get(name, {})))
    except Exception as e:
        log.warning("cache write failed: %s", e)


def get(name: str, key: str):
    return load(name).get(key)


def put(name: str, key: str, value) -> None:
    load(name)[key] = value
    save(name)
