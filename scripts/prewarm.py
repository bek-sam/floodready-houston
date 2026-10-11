"""FloodReady cache prewarm. Usage: python prewarm.py [BASE_URL]  (argv[1] or env BASE, default http://localhost:8000).
Hits demo addresses/routes twice (cold pass, then warm pass) and prints timing + speedup.
Never calls /ask, /plan or /push (rate limits / cost)."""
import os
import sys
import time

import httpx

args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (args[0] if args else os.environ.get("BASE", "http://localhost:8000")).rstrip("/")
API = BASE + "/api"
c = httpx.Client(timeout=60, follow_redirects=True)

ADDRS = ["1200 Main St, Houston, TX", "Meyerland, Houston, TX", "Allen Parkway, Houston, TX"]
PLACES = [(29.6847, -95.4698), (29.7648, -95.3665), (29.68, -95.46), (29.564, -95.025)]  # last = Seabrook 77586
ROUTE = {"origin": {"lat": 29.7648, "lon": -95.3665}, "destination": {"lat": 29.7648, "lon": -95.356}}


def build():
    calls = []  # (label, method, path, params, body)
    g = lambda label, path, **p: calls.append((label, "GET", path, p, None))
    for a in ADDRS:
        g(f"geocode {a[:18]}", "/geocode", q=a)
    for lat, lon in PLACES:
        pt = {"lat": lat, "lon": lon}
        t = f"{lat},{lon}"
        g(f"risk {t}", "/risk", **pt)
        g(f"flood-history {t}", "/flood-history", **pt)
        g(f"alerts {t}", "/alerts", **pt)
        g(f"civic {t}", "/civic", **pt)
        g(f"evac {t}", "/evac", **pt)
        g(f"rain24 {t}", "/rain24", **pt)
        g(f"medical {t}", "/medical", **pt)
        g(f"shelters {t}", "/shelters", **pt)
        g(f"outlook {t}", "/outlook", **pt)
    g("zip-insurance 77096", "/zip-insurance", zip="77096")
    g("zip-insurance 77025", "/zip-insurance", zip="77025")
    g("zip-insurance 77586", "/zip-insurance", zip="77586")
    g("crossings", "/crossings")
    g("buyout-area", "/buyout-area")
    g("insurance/countdown", "/insurance/countdown", purchase_date="2026-10-10")
    g("route-check/demo", "/route-check/demo")
    g("route-check/demo storm", "/route-check/demo", simulate="storm")
    calls.append(("route-check", "POST", "/route-check", {}, ROUTE))
    calls.append(("route-check storm", "POST", "/route-check", {"simulate": "storm"}, ROUTE))
    return calls


def run(label, method, path, params, body):
    t = time.time()
    try:
        r = c.request(method, API + path, params=params, json=body)
        status = r.status_code
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
    except Exception as e:
        return time.time() - t, f"ERR {type(e).__name__}", None
    return time.time() - t, status, data


def pass_(calls, title):
    print(f"\n== {title} ==")
    out = {}
    for call in calls:
        dt, st, data = run(*call)
        out[call[0]] = dt
        print(f"{st!s:>8} {call[0]:<34} {dt:6.2f}s", flush=True)
        if call[0] == "replay/events" and isinstance(data, (list, dict)):
            pass
    return out


def dynamic():
    """Replay files and gauge history depend on server data: discover ids."""
    calls = []
    _, st, ev = run("replay/events", "GET", "/replay/events", {}, None)
    ev = ev.get("events", ev) if isinstance(ev, dict) else ev
    calls.append(("replay/events", "GET", "/replay/events", {}, None))
    gauge = None
    for e in ev or []:
        calls.append((f"replay/{e['id']}", "GET", f"/replay/{e['id']}", {}, None))
        if not gauge:
            _, _, d = run("", "GET", f"/replay/{e['id']}", {}, None)
            if d and d.get("gauges"):
                gauge = d["gauges"][0].get("id") or d["gauges"][0].get("site_no")
    if gauge:
        calls.append((f"gauge history {gauge}", "GET", f"/gauges/{gauge}/history", {"hours": 48}, None))
    return calls


calls = build() + dynamic()
print(f"Prewarming {BASE} ({len(calls)} calls; skipping /ask /plan /push)")
t0 = time.time()
a = pass_(calls, "pass 1 (cold)")
b = pass_(calls, "pass 2 (warm)")
ta, tb = sum(a.values()), sum(b.values())
print("\n== speedup ==")
for k in sorted(a, key=lambda k: a[k] - b[k], reverse=True)[:8]:
    print(f"{k:<34} {a[k]:6.2f}s -> {b[k]:6.2f}s  x{a[k] / max(b[k], 0.001):.1f}")
print(f"\nTOTAL pass1 {ta:.2f}s  pass2 {tb:.2f}s  speedup x{ta / max(tb, 0.001):.1f}  (wall {time.time() - t0:.1f}s)")
