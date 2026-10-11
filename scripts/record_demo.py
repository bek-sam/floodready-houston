"""Record demo snapshots for offline mode. Usage (from backend/): uv run python ../scripts/record_demo.py [BASE] [ASK_BASE]
BASE (default http://localhost:8000) is the running backend; ASK_BASE (default http://localhost:8070) must be a
backend started with GEMINI_API_KEY= ELEVENLABS_API_KEY= so canned Ask answers come from the knowledge cards/templates.
Never calls /plan, /voice or live. Writes data/demo_snapshot/*.json (served by app/demo_snapshot.py)."""
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.demo_snapshot import SNAP_DIR, file_name, make_key  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (args[0] if args else "http://localhost:8000").rstrip("/")
ASK = (args[1] if len(args) > 1 else "http://localhost:8070").rstrip("/")
c = httpx.Client(timeout=90, follow_redirects=True)
NOW = datetime.now().astimezone().isoformat(timespec="seconds")
SNAP_DIR.mkdir(parents=True, exist_ok=True)
for f in SNAP_DIR.glob("*.json"):
    f.unlink()
saved, failed = 0, []

PLACES = [(29.6876, -95.4583), (29.564, -95.025), (29.6847, -95.4698), (29.68, -95.46), (29.7869, -95.644)]
ROUTE = {"origin": {"lat": 29.7648, "lon": -95.3665}, "destination": {"lat": 29.7648, "lon": -95.356}}
PITCH = [("Did my neighborhood flood before?", "en", True), ("¿Qué hago si mi calle se inunda?", "es", False),
         ("My street is flooding, what do I do?", "es", False), ("Do I need flood insurance and how long is the wait?", "en", False),
         ("Where is the nearest shelter?", "en", True), ("Who do I call about a flooded street?", "en", False)]


def save(method, path, params=None, body=None, base=BASE, **extra):
    global saved
    full = "/api" + path
    try:
        r = c.request(method, base + full, params=params, json=body)
        data = r.json()
    except Exception as e:  # noqa: BLE001
        failed.append(f"{method} {path} {params}: {type(e).__name__}")
        return None
    if r.status_code >= 400:
        failed.append(f"{method} {path} {params}: {r.status_code}")
        return None
    q = str(r.request.url.query, "ascii") if isinstance(r.request.url.query, bytes) else r.request.url.query
    key = make_key(method, full, q, json.dumps(body).encode() if body is not None else None)
    entry = {"key": key, "method": method, "path": full, "query": q, "status": r.status_code, "recorded_at": NOW, "body": data, **extra}
    (SNAP_DIR / file_name(key)).write_text(json.dumps(entry, ensure_ascii=False))
    saved += 1
    return data


g = lambda path, **p: save("GET", path, p or None)  # noqa: E731

for lat, lon in PLACES:
    pt = {"lat": lat, "lon": lon}
    risk = g("/risk", **pt)
    g("/alerts", **pt)
    g("/outlook", **pt)
    g("/flood-history", **pt)
    g("/evac", **pt)
    g("/hwm", radius_mi=2, **pt)
    g("/civic", **pt)
    g("/shelters", **pt)
    g("/shelters", pet_friendly="false", limit=10, **pt)
    g("/medical", **pt)
    g("/medical", kind="dialysis", limit=5, **pt)
    g("/buyout-area", **pt)
    g("/rain24", **pt)
    g("/parking/check", **pt)
    g("/nri", **pt)
    g("/reservoir/pool", **pt)
    for gg in (risk or {}).get("nearest_gauges", [])[:3]:
        g(f"/gauges/{gg['id']}/history", hours=48)
g("/flood-history", lat=29.6876, lon=-95.4583, zip="77096")
g("/flood-history", lat=29.6847, lon=-95.4698, zip="77096")
for z in ("77096", "77025", "77586"):
    g("/zip-insurance", zip=z)
for z in ("77096", "77025", "77586", "77079"):
    g("/empower", zip=z)
g("/airports/status")
g("/declarations", county="Harris", state="TX")
g("/coastal")
g("/crossings")
g("/status")
g("/insurance/countdown", purchase_date="2026-10-10")
for a in ("5300 N Braeswood Blvd, Houston, TX 77096", "Seabrook, TX 77586", "Meyerland, Houston, TX"):
    g("/geocode", q=a)
g("/harvey/extent", bbox="-95.4683,29.6776,-95.4483,29.6976", limit=300)

for sim in (None, "storm"):
    p = {"simulate": sim} if sim else None
    demo = save("GET", "/route-check/demo", p) or []
    for d in demo:
        save("POST", "/route-check", p, {"origin": d["origin"], "destination": d["destination"]})
    save("POST", "/route-check", p, ROUTE)

ev = g("/replay/events") or []
ev = ev.get("events", ev) if isinstance(ev, dict) else ev
for e in ev:
    g(f"/replay/{e['id']}")
g("/replay/harvey-2017")

for q, lang, loc in PITCH:
    body = {"question": q, "lang": lang, **({"lat": 29.6847, "lon": -95.4698} if loc else {})}
    d = save("POST", "/ask", None, body, base=ASK, question=q, lang=lang, canned=True)
    if d:
        print(f"ask [{lang}] {q[:40]!r} -> {d.get('generated_by')}")

print(f"saved {saved} snapshots to {SNAP_DIR}; {len(failed)} failed")
for f in failed:
    print("  FAIL", f)
