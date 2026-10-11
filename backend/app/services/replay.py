from app.config import DATA_DIR
from app.services.data import load_json


def list_events() -> list[dict]:
    idx = load_json("replay/events.json")
    if isinstance(idx, list) and idx:
        return idx
    out = []
    d = DATA_DIR / "replay"
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        if p.name == "events.json":
            continue
        ev = (load_json(f"replay/{p.name}", {}) or {}).get("event") or {}
        out.append({"id": ev.get("id", p.stem), "name": ev.get("name", p.stem), "start": ev.get("start"),
                    "end": ev.get("end"), "summary": ev.get("summary"), "source": ev.get("source")})
    return out


def get_event(event_id: str) -> dict | None:
    if event_id == "events" or not event_id.replace("-", "").replace("_", "").isalnum():
        return None
    return load_json(f"replay/{event_id}.json")
