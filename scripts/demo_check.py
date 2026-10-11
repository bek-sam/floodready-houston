"""FloodReady pre-demo smoke check. Usage: python demo_check.py [BASE_URL] [--front URL]
BASE_URL (argv[1] or env BASE, default http://localhost:8000). Exit 1 on any failure."""
import os
import sys
import time

import httpx

args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (args[0] if args else os.environ.get("BASE", "http://localhost:8000")).rstrip("/")
FRONT = None
if "--front" in sys.argv:
    i = sys.argv.index("--front")
    FRONT = sys.argv[i + 1] if i + 1 < len(sys.argv) else "http://localhost:5173"
    if FRONT in args:
        args.remove(FRONT)
API = BASE + "/api"
MEY = {"lat": 29.6847, "lon": -95.4698}
c = httpx.Client(timeout=30, follow_redirects=True)
results = []


def step(name, fn):
    t = time.time()
    try:
        detail = fn() or ""
        ok = True
    except Exception as e:
        ok, detail = False, f"{type(e).__name__}: {e}"[:160]
    dt = time.time() - t
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name:<28} {dt:5.2f}s {detail}", flush=True)


def get(path, **p):
    r = c.get(API + path, params=p)
    r.raise_for_status()
    return r.json()


def post(path, body, **p):
    r = c.post(API + path, json=body, params=p)
    r.raise_for_status()
    return r.json()


def ok(cond, msg="assertion failed"):
    if not cond:
        raise AssertionError(msg)


def s1():
    d = get("/health")
    ok(d.get("status") == "ok", d)
    k = d.get("keys", {})
    for n in ("gemini", "elevenlabs", "backboard", "db"):
        ok(isinstance(k.get(n), bool), f"keys.{n}")
    return str(k)


def s2():
    d = get("/risk", **MEY)
    ok(d["harvey"]["flooded"] is True, "harvey.flooded")
    ok(d.get("fema_zone") == "AE", d.get("fema_zone"))
    ok(d.get("elevation_ft") is not None, "elevation")
    ok(str(d["harvey"].get("source", "")).startswith("https"), "harvey.source")
    return f"zone={d['fema_zone']} elev={d['elevation_ft']}"


def s3():
    d = get("/flood-history", **MEY)
    ok(d["harvey"]["flooded"] is True, "flooded")
    ids = {e.get("id") for e in d["events"]}
    ok({"taxday-2016", "harvey-2017"} <= ids, ids)
    hv = next(e for e in d["events"] if e["id"] == "harvey-2017")
    ok(hv["nearest_gauge"]["peak_category"] == "major", "peak_category")
    return f"{len(d['events'])} events"


def s4():
    d = get("/route-check/demo", simulate="storm")
    ok(len(d) >= 1, "empty")
    ok("Allen" in str(d), "no Allen label")
    return f"{len(d)} routes"


BODY = {"origin": {"lat": 29.7648, "lon": -95.3665}, "destination": {"lat": 29.7648, "lon": -95.356}}


def s5():
    d = post("/route-check", BODY, simulate="storm")
    ok(d["verdict"] == "avoid", d["verdict"])
    ok(len(d["hazards"]) >= 1, "hazards")
    ok(d["route"]["coordinates"], "coords")
    return f"hazards={len(d['hazards'])}"


def s6():
    d = post("/route-check", BODY)
    ok(d["verdict"] in ("safe", "caution", "avoid"), d["verdict"])
    return d["verdict"]


def ask(body):
    try:
        return post("/ask", body)
    except Exception:
        return post("/ask", body)  # retry once: cold index


def s7():
    d = ask({"question": "My street is flooding, what do I do?", "lang": "es"})
    ok("911" in d["answer"], "no 911")
    ok(isinstance(d["sources"], list), "sources")
    return d.get("generated_by", "")


def s8():
    d = ask({"question": "Did my neighborhood flood before?", "lang": "en", **MEY})
    ok("Harvey" in d["answer"], "no Harvey")


def s9():
    d = get("/shelters", lat=29.68, lon=-95.46)
    ok(d["any_open"] is False, "any_open")
    ok(d["historical"] is True, "historical")
    ok(len(d["shelters"]) >= 1, "none")
    ok("311" in d["note"], "note")
    return f"{len(d['shelters'])} shelters"


def s10():
    d = get("/zip-insurance", zip="77096")["claims"]
    ok(d["total"] >= 6000, d["total"])
    ok(d["since_2017"] > 0, "since_2017")
    ok(d["by_year"], "by_year")
    return f"total={d['total']}"


def s11():
    d = get("/crossings")
    ok(d["type"] == "FeatureCollection" and len(d["features"]) >= 1, "features")
    for f in d["features"]:
        p = f["properties"]
        ok(p.get("id") and p.get("name"), "id/name")
        ok(p.get("risk") in ("high", "medium"), p.get("risk"))
        ok(p.get("sources"), "sources")
    return f"{len(d['features'])} crossings"


def s12():
    ev = get("/replay/events")
    ev = ev.get("events", ev) if isinstance(ev, dict) else ev
    ok(ev, "no events")
    d = get(f"/replay/{ev[0]['id']}")
    ok(d["gauges"], "gauges")
    g = d["gauges"][0]
    ok(g["series"], "series")
    ok({"action", "minor", "moderate", "major"} <= set(g["flood_stages"]), "flood_stages")
    return ev[0]["id"]


def s13():
    d = get("/insurance/countdown", purchase_date="2026-10-10")
    ok(d["days_wait"] == 30, d["days_wait"])
    ok(d.get("source"), "source")


def s14():
    d = get("/alerts", **MEY)
    ok("alerts" in d, "alerts key")
    return f"{len(d['alerts'])} alerts"


def s15():
    d = get("/medical", lat=29.68, lon=-95.46)
    ok(d, "empty")
    return ",".join(d) if isinstance(d, dict) else ""


def s16():
    p = post("/watch", {"label": "demo_check", "lat": 29.6847, "lon": -95.4698, "lang": "en"})
    d = get("/watch/status", ids=p["id"], simulate="storm")
    lv = d["places"][0]["level"]
    ok(lv in ("watch", "warning"), lv)
    return lv


def s17():
    d = post("/plan", {"profile": {"household_size": 2, "has_pets": False}, **MEY})
    ok(d["steps"], "steps")
    ok(d["generated_by"] in ("gemini", "template"), d["generated_by"])
    return d["generated_by"]


def s18():
    if not FRONT:
        return "skipped (no --front)"
    r = c.get(FRONT)
    ok(r.status_code == 200, r.status_code)


def x1():
    r = c.post(API + "/ask", json={"question": "x" * 600, "lang": "en"})
    ok(r.status_code == 422, r.status_code)


def x2():
    r = c.post(API + "/push/test", json={})
    ok(r.status_code == 400, r.status_code)  # no real notification sent


def x3():
    ok(get("/push/vapid-public-key").get("key"), "no key")


for i, (n, f) in enumerate([
    ("health", s1), ("risk", s2), ("flood-history", s3), ("route-demo", s4),
    ("route-check storm", s5), ("route-check live", s6), ("ask es 911", s7),
    ("ask harvey", s8), ("shelters", s9), ("zip-insurance", s10), ("crossings", s11),
    ("replay", s12), ("insurance countdown", s13), ("alerts", s14), ("medical", s15),
    ("watch status storm", s16), ("plan", s17), ("frontend", s18),
    ("ask 600ch 422", x1), ("push 400 no endpoint", x2), ("vapid key", x3)], 1):
    step(f"{i:02d} {n}", f)

t0 = time.time()
bad = results.count(False)
print(f"\n{results.count(True)}/{len(results)} passed" + (f", {bad} FAILED" if bad else ""))
sys.exit(1 if bad else 0)
