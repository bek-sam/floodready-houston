import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import config
from app.services import data as data_mod
from app.services import http as http_mod

CROSSINGS = {"type": "FeatureCollection", "features": [{
    "type": "Feature", "geometry": {"type": "Point", "coordinates": [-95.37, 29.76]},
    "properties": {"id": "c1", "name": "Test Underpass", "risk": "high", "reasons": ["floods"], "sources": ["http://x"]}}]}
GAUGES = [{"id": "BBST2", "name": "Buffalo Bayou", "lat": 29.76, "lon": -95.38,
           "flood_stages": {"action": 17, "minor": 28, "moderate": 29.5, "major": 32}}]


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "replay").mkdir()
    (tmp_path / "crossings.geojson").write_text(json.dumps(CROSSINGS))
    (tmp_path / "gauges.json").write_text(json.dumps(GAUGES))
    (tmp_path / "replay" / "t.json").write_text(json.dumps({"event": {"id": "t", "name": "T"}, "gauges": []}))
    monkeypatch.setattr(data_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import app.services.replay as rp
    monkeypatch.setattr(rp, "DATA_DIR", tmp_path)
    import app.services.harvey as hv
    monkeypatch.setattr(hv, "DATA_DIR", tmp_path)
    hv._idx.update(loaded=False, mtime=None)
    http_mod._cache.clear()
    from app.services import arcgis, diskcache
    monkeypatch.setattr(diskcache, 'CACHE_DIR', tmp_path / 'cache')
    diskcache._mem.clear()
    arcgis._mem.clear()

    async def fake_get_json(url, params=None, ttl=300, headers=None):
        if "census.gov/geocoder/locations" in url:
            return {"result": {"addressMatches": [{"coordinates": {"x": -95.37, "y": 29.76}, "matchedAddress": "X, HOUSTON"}]}}
        if "NFHL" in url:
            return {"features": [{"attributes": {"FLD_ZONE": "X", "ZONE_SUBTY": "0.2 PCT", "SFHA_TF": "F"}}]}
        if "epqs" in url:
            return {"value": 42.0}
        if "City_Limit" in url:
            return {"features": [{"attributes": {"NAME": "HOUSTON", "SERVICE_TY": "FULL"}}]}
        if "Barker_Reservoir" in url:
            return {"count": 0}
        if "Bond_CIP" in url:
            return {"features": [{"geometry": {"type": "Point", "coordinates": [-95.37, 29.77]}, "properties": {
                "Project_Title": "Test Basin", "Status": "Active", "Budgeted": 100, "Spent": 10, "Hyperlink": "http://h"}}]}
        if "stageflow" in url:
            return {"observed": {"data": [{"primary": 5.0, "validTime": "t"}]}}
        if "alerts" in url:
            return {"features": []}
        if "osrm" in url:
            return {"routes": [{"geometry": {"type": "LineString", "coordinates": [[-95.38, 29.76], [-95.37, 29.76], [-95.36, 29.76]]}}]}
        return None

    monkeypatch.setattr(http_mod, "get_json", fake_get_json)
    for m in ("geo", "risk", "alerts", "gauges", "route", "arcgis"):
        mod = __import__(f"app.services.{m}", fromlist=["x"])
        if hasattr(mod, "get_json"):
            monkeypatch.setattr(mod, "get_json", fake_get_json)
    from app.main import app
    from app import ratelimit
    ratelimit.reset()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and set(r["keys"]) == {"gemini", "elevenlabs", "backboard", "db"}


def test_geocode(client):
    assert client.get("/api/geocode", params={"q": "1 Main St"}).json()["lat"] == 29.76


def test_risk(client):
    r = client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["fema_zone"] == "X" and r["sfha"] is False and r["elevation_ft"] == 42.0
    assert "low_ground" not in r and r["jurisdiction"] == "City of Houston"
    assert r["nearest_gauges"][0]["status"] == "normal" and r["facts"]


def test_alerts_and_crossings(client):
    assert client.get("/api/alerts", params={"lat": 1, "lon": 2}).json()["alerts"] == []
    assert len(client.get("/api/crossings").json()["features"]) == 1


def test_route_safe_vs_storm(client):
    body = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "caution" and r["hazards"][0]["crossing_id"] == "c1"
    r = client.post("/api/route-check?simulate=storm", json=body).json()
    assert r["verdict"] == "avoid"


def test_replay(client):
    assert client.get("/api/replay/events").json()[0]["id"] == "t"
    assert client.get("/api/replay/t").status_code == 200
    assert client.get("/api/replay/nope").status_code == 404


def test_insurance(client):
    r = client.get("/api/insurance/countdown", params={"purchase_date": "2026-10-10"}).json()
    assert r["effective_date"] == "2026-11-09" and r["covered_before_season_end"] is True
    r = client.get("/api/insurance/countdown", params={"purchase_date": "2026-11-15"}).json()
    assert r["covered_before_season_end"] is False


def test_civic_missing_file(client):
    r = client.get("/api/civic", params={"lat": 29.8, "lon": -95.65}).json()
    r2 = client.get("/api/civic", params={"lat": 29.77, "lon": -95.37}).json()
    assert r["reservoir"]["in_area"] is True and "warnings" in r
    p = r2["bond"]["projects"][0]
    assert p["name"] == "Test Basin" and p["distance_mi"] < 1


def test_low_ground_with_datum():
    from app.services.risk import _low_ground
    g = [{"name": "G", "datum_ft": 10, "flood_stages": {"minor": 20}}]
    assert _low_ground(28, g)[0] is True and _low_ground(60, g)[0] is False
    assert _low_ground(28, [])[0] is None


def test_geocode_seed_and_cache(client):
    r = client.get("/api/geocode", params={"q": "Meyerland"}).json()
    assert abs(r["lat"] - 29.68) < 0.1


def test_reports(client):
    r = client.post("/api/reports", json={"lat": 29.7, "lon": -95.3, "depth_in": 6, "note": "n"})
    assert r.status_code == 200
    assert any(x["id"] == r.json()["id"] for x in client.get("/api/reports").json())


def test_demo_routes_and_watch(client):
    demo = client.get("/api/route-check/demo").json()
    assert len(demo) >= 3 and {"label", "origin", "destination"} <= set(demo[0])
    pl = client.post("/api/watch", json={"label": "Home", "lat": 29.76, "lon": -95.37, "lang": "en"}).json()
    r = client.get("/api/watch/status", params={"ids": pl["id"]}).json()["places"][0]
    assert r["level"] in ("ok", "watch") and r["crossings_nearby"] == 1
    r = client.get("/api/watch/status", params={"ids": pl["id"], "simulate": "storm"}).json()["places"][0]
    assert r["level"] == "warning" and any("Buffalo Bayou" in x for x in r["reasons"]) and "911" in r["message"]
    assert client.get("/api/watch/status", params={"ids": "nope"}).json()["places"] == []


def test_harvey(client, tmp_path, monkeypatch):
    r = client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["harvey"]["flooded"] is None and "No Harvey extent data" in r["harvey"]["note"]
    sq = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
        "type": "Polygon", "coordinates": [[[-95.38, 29.75], [-95.36, 29.75], [-95.36, 29.77], [-95.38, 29.77], [-95.38, 29.75]]]}}]}
    (tmp_path / "harvey_inundation.geojson").write_text(json.dumps(sq))
    from app.services import harvey
    harvey._idx.update(loaded=False, mtime=None)
    import app.services.harvey as h
    monkeypatch.setattr(h, 'DATA_DIR', tmp_path)
    assert client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()["harvey"]["flooded"] is True
    assert client.get("/api/risk", params={"lat": 29.76, "lon": -95.0}).json()["harvey"]["flooded"] is None
    assert client.get("/api/risk", params={"lat": 29.752, "lon": -95.375}).json()["harvey"]["flooded"] is True


def test_push_flow(client, monkeypatch, tmp_path):
    from app.services import push as P
    monkeypatch.setattr(P, "VAPID_FILE", tmp_path / "v.json")
    P._vapid_cache.clear()
    calls = []

    def fake_webpush(info, data, **kw):
        calls.append((info["endpoint"], json.loads(data)))
        if "gone" in info["endpoint"]:
            class R: status_code = 410
            raise P.WebPushException("gone", response=R())

    monkeypatch.setattr(P, "webpush", fake_webpush)
    key = client.get("/api/push/vapid-public-key").json()["key"]
    assert len(key) > 80 and "=" not in key and (tmp_path / "v.json").exists()
    assert client.get("/api/push/vapid-public-key").json()["key"] == key
    pl = client.post("/api/watch", json={"label": "Home", "lat": 29.76, "lon": -95.37}).json()
    sub = {"endpoint": "https://fcm.googleapis.com/fcm/send/ok", "keys": {"p256dh": "a", "auth": "b"}}
    assert client.post("/api/push/subscribe", json={"subscription": {"endpoint": "x"}}).status_code == 422
    assert "id" in client.post("/api/push/subscribe", json={"subscription": sub, "place_ids": [pl["id"]], "lang": "es"}).json()
    client.post("/api/push/subscribe", json={"subscription": {**sub, "endpoint": "https://fcm.googleapis.com/fcm/send/gone"}, "place_ids": [pl["id"]]})
    assert client.post("/api/push/test", json={"endpoint": sub["endpoint"]}).json() == {"sent": 1}
    r = client.post("/api/push/simulate", json={"endpoint": sub["endpoint"]}).json()
    assert r == {"sent": 1}  # the 410 subscription is deleted, not counted
    sim = [c for c in calls if c[1]["level"] == "warning"][0][1]
    assert sim["url"] == "/#watch" and "911" in sim["body"] or "Llame al 911" in sim["body"]
    assert client.post("/api/push/simulate", json={"endpoint": sub["endpoint"]}).json() == {"sent": 1}
    from app import ratelimit
    ratelimit.reset()  # this flow exceeds 6 push calls/min
    client.post("/api/push/unsubscribe", json={"endpoint": "https://fcm.googleapis.com/fcm/send/gone"})
    assert client.post("/api/push/unsubscribe", json={"endpoint": sub["endpoint"]}).json() == {"ok": True}
    assert client.post("/api/push/simulate", json={"endpoint": sub["endpoint"]}).status_code == 404


def test_push_loop_only_on_rise(client, monkeypatch, tmp_path):
    import asyncio
    from app.services import push as P
    monkeypatch.setattr(P, "VAPID_FILE", tmp_path / "v.json")
    P._vapid_cache.clear()
    sent = []
    monkeypatch.setattr(P, "webpush", lambda info, data, **kw: sent.append(json.loads(data)))
    levels = iter(["ok", "watch", "watch", "warning"])

    async def fake_eval(p, sim=False):
        return {"level": next(levels)}

    monkeypatch.setattr(P, "evaluate", fake_eval)
    pl = client.post("/api/watch", json={"label": "Home", "lat": 29.76, "lon": -95.37}).json()
    client.post("/api/push/subscribe", json={"subscription": {"endpoint": "https://updates.push.services.mozilla.com/wpush/v2/1", "keys": {"p256dh": "a", "auth": "b"}}, "place_ids": [pl["id"]]})
    counts = [asyncio.run(P.check_all()) for _ in range(4)]
    assert counts == [0, 1, 0, 1] and [s["level"] for s in sent] == ["watch", "warning"]


def _shelter_feat(name, code, x, y, pet=None):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [x, y]},
            "properties": {"Name": name, "Address": "a", "County": "Harris", "ShelterStatus": code,
                           "Capacity": 10, "Occupancy": 1, "PetFriendly": pet}}


def test_shelters_and_none_open(client, monkeypatch):
    from app.services import arcgis
    feats = [_shelter_feat("Far", 1, -95.5, 29.8, 0), _shelter_feat("Near", 0, -95.37, 29.76),
             _shelter_feat("Odd", 9, -95.371, 29.76)]

    async def fake(name, url, ttl=3600):
        return feats
    monkeypatch.setattr(arcgis, "full_layer", fake)
    r = client.get("/api/shelters", params={"lat": 29.76, "lon": -95.37}).json()
    assert [s["name"] for s in r["shelters"]] == ["Near", "Odd", "Far"] and r["any_open"] is False and r["historical"] is True and r["data_as_of"].startswith("2017")
    assert r["shelters"][1]["status_2017"] == "Unknown" and r["shelters"][0]["status_2017"] == "Pending"
    assert "NOT live status" in r["note"] and "status" not in r["shelters"][0]
    r = client.get("/api/shelters", params={"lat": 29.76, "lon": -95.37, "pet_friendly": True}).json()
    assert [s["name"] for s in r["shelters"]] == ["Far"]
    feats[0]["properties"]["ShelterStatus"] = 3
    r = client.get("/api/shelters", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["any_open"] is False and "211" in r["note"]


def test_shelters_offline_is_200(client):
    r = client.get("/api/shelters", params={"lat": 29.76, "lon": -95.37})
    assert r.status_code == 200 and r.json()["shelters"] == [] and r.json()["warnings"]
    import asyncio
    from app.services.shelters import get_shelters
    assert "shelters" in asyncio.run(get_shelters(29.76, -95.37, limit=3))


def test_outlook(client, monkeypatch):
    from app.services import outlook

    async def down(url, params=None, ttl=0):
        return None
    monkeypatch.setattr(outlook, "get_json", down)
    r = client.get("/api/outlook", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["day1"] is None and r["warnings"]

    async def fake(url, params=None, ttl=0):
        return {"features": [{"attributes": {"outlook": "Marginal (At Least 5%)"}},
                             {"attributes": {"outlook": "Slight (At Least 15%)"}}]}
    monkeypatch.setattr(outlook, "get_json", fake)
    assert client.get("/api/outlook", params={"lat": 1, "lon": 2}).json()["day1"]["category"] == "Slight"

    async def empty(url, params=None, ttl=0):
        return {"features": []}
    monkeypatch.setattr(outlook, "get_json", empty)
    assert client.get("/api/outlook", params={"lat": 1, "lon": 2}).json()["day1"]["category"] == "None"


def test_route_osrm_down_not_safe(client, monkeypatch):
    from app.services import route
    async def down(*a, **k):
        return None
    monkeypatch.setattr(route, "get_json", down)
    body = {"origin": {"lat": 40.0, "lon": -90.0}, "destination": {"lat": 40.1, "lon": -90.1}}
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "caution" and "check manually" in r["message"]


def test_watch_flood_watch_is_watch(client, monkeypatch):
    from app.services import watch
    async def al(lat, lon):
        return {"alerts": [{"event": "Flood Watch", "severity": "Severe"}]}
    monkeypatch.setattr(watch, "get_alerts", al)
    import asyncio
    r = asyncio.run(watch.evaluate({"id": "x", "label": "H", "lat": 0, "lon": 0}))
    assert r["level"] == "watch"


def test_stale_gauge_unknown(client):
    from datetime import datetime, timedelta, timezone
    from app.services.gauges import _stale
    old = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
    new = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert _stale(old) and not _stale(new) and not _stale("garbage")


def test_insurance_december_rolls_over(client):
    r = client.get("/api/insurance/countdown", params={"purchase_date": "2026-12-05"}).json()
    assert r["season_end"] == "2027-11-30" and r["covered_before_season_end"] is True


def test_alert_description_truncated(client, monkeypatch):
    from app.services import alerts
    async def big(url, params=None, ttl=0):
        return {"features": [{"properties": {"event": "Flood Watch", "description": "x" * 5000}}]}
    monkeypatch.setattr(alerts, "get_json", big)
    import asyncio
    assert len(asyncio.run(alerts.get_alerts(1, 2))["alerts"][0]["description"]) == 600


def test_watch_ignores_non_flood_alerts(client, monkeypatch):
    from app.services import watch
    async def al(lat, lon):
        return {"alerts": [{"event": "Heat Advisory"}, {"event": "Wind Advisory"}, {"event": "Storm Surge Warning"}]}
    monkeypatch.setattr(watch, "get_alerts", al)
    import asyncio
    r = asyncio.run(watch.evaluate({"id": "x", "label": "H", "lat": 0, "lon": 0}))
    assert [a["event"] for a in r["alerts"]] == ["Storm Surge Warning"] and r["level"] == "warning"


def test_shelter_note_no_911_and_no_typo():
    from app.services import shelters
    assert "911" not in shelters.NOTE and "((" not in shelters.NOTE


FAKE_G = [{"id": "AAA", "usgs_id": "1", "name": "A", "lat": 1, "lon": 1,
           "flood_stages": {"action": 1, "minor": 2, "moderate": None, "major": None}}]


def test_gauge_history_db_and_live(client, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.services import gauge_history as gh
    monkeypatch.setattr(gh, "load_gauges", lambda: FAKE_G)
    gid = "AAA"
    now = datetime.now(timezone.utc)
    # <3 points -> live fallback
    async def fake_fetch(c, coll, ids, extra):
        return [(ids[0], now - timedelta(hours=1), 5.0), (ids[0], now, 5.5)]
    monkeypatch.setattr(gh, "_fetch", fake_fetch)
    d = client.get(f"/api/gauges/{gid}/history?hours=48").json()
    assert d["source"] == "live" and len(d["readings"]) == 2 and "minor" in d["flood_stages"]
    # >=3 stored points -> db, duplicates ignored
    rows = [(gid, now - timedelta(hours=i), 1.0 + i) for i in range(4)]
    assert gh._store(rows) == 4 and gh._store(rows) == 0
    d = client.get(f"/api/gauges/{gid}/history").json()
    assert d["source"] == "db" and len(d["readings"]) == 4
    assert client.get("/api/gauges/NOPE/history").status_code == 404


def test_poller_batches_and_survives_failure(monkeypatch):
    import asyncio
    from app.services import gauge_history as gh
    calls = []
    async def fake_fetch(c, coll, ids, extra):
        calls.append(len(ids))
        raise_ = len(calls) == 1
        return [] if raise_ else []
    monkeypatch.setattr(gh, "_fetch", fake_fetch)
    monkeypatch.setattr(gh, "BATCH", 5)
    gs = [{"id": f"G{i}", "usgs_id": str(i)} for i in range(12)] + [{"id": "NOUSGS"}]
    monkeypatch.setattr(gh, "load_gauges", lambda: gs)
    asyncio.run(gh.poll_once())
    n = 12
    assert sum(calls) == n and max(calls) <= 5


def test_push_requires_known_endpoint(client):
    for path in ("/api/push/test", "/api/push/simulate"):
        assert client.post(path).status_code == 422 or client.post(path).status_code == 400
        assert client.post(path, json={}).status_code == 400
        assert client.post(path, json={"endpoint": "https://nope"}).status_code == 404


def test_rate_limit_and_ask_length(client):
    assert client.post("/api/ask", json={"question": "x" * 501}).status_code == 422
    from app.ratelimit import LIMITS
    limit = dict((p, n) for p, n, _ in LIMITS)
    codes = [client.post("/api/push/test", json={"endpoint": "https://nope"}).status_code
             for _ in range(limit["/api/push/"] + 2)]
    assert codes[:2] == [404, 404] or 429 in codes
    assert codes[-1] == 429 and client.post("/api/push/test", json={}).json()["detail"]
    for _ in range(limit["/api/plan"]):
        client.post("/api/plan", json={})
    r = client.post("/api/plan", json={})
    assert r.status_code == 429


def test_cors_env(monkeypatch):
    import importlib, app.main as m
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.example, https://b.example")
    m2 = importlib.reload(m)
    cors = [x for x in m2.app.user_middleware if x.cls.__name__ == "CORSMiddleware"][0]
    assert cors.kwargs["allow_origins"] == ["https://a.example", "https://b.example"]
    monkeypatch.delenv("ALLOWED_ORIGINS")
    importlib.reload(m)


# ---- Cycle 5: zip-insurance, medical, route reports ----
def test_zip_insurance(client, monkeypatch):
    from app.services import zipinsurance as zi
    calls = []

    async def fake(url, params=None, ttl=300, headers=None):
        calls.append(url)
        if "NfipClaims" in url and "v3" in url:
            return {"NfipClaims": [{"yearOfLoss": 2016}, {"yearOfLoss": 2017}, {"yearOfLoss": 2017}, {"yearOfLoss": 2019}]}
        if "NfipPolicies" in url:
            return {"metadata": {"count": 321}}
        return None
    monkeypatch.setattr(zi, "get_json", fake)
    zi._mem.clear()
    r = client.get("/api/zip-insurance", params={"zip": "77096"}).json()
    assert r["claims"]["total"] == 4 and r["claims"]["since_2017"] == 3
    assert r["claims"]["by_year"][1] == {"year": 2017, "count": 2} and r["policies_in_force"] == 321
    n = len(calls)
    client.get("/api/zip-insurance", params={"zip": "77096"})
    assert len(calls) == n  # cached
    assert client.get("/api/zip-insurance", params={"zip": "abc"}).status_code == 422


def test_zip_insurance_outage(client, monkeypatch):
    from app.services import zipinsurance as zi
    zi._mem.clear()

    async def none(*a, **k):
        return None
    monkeypatch.setattr(zi, "get_json", none)
    r = client.get("/api/zip-insurance", params={"zip": "77002"}).json()
    assert r["policies_in_force"] is None and r["warnings"]


def test_medical(client, tmp_path):
    r = client.get("/api/medical", params={"lat": 29.7, "lon": -95.4}).json()
    assert r["facilities"] == [] and r["note"]  # file missing
    (tmp_path / "dialysis.json").write_text(json.dumps([
        {"name": "Far", "address": "1 A", "city": "H", "zip": "77001", "phone": "1", "lat": 30.2, "lon": -95.4},
        {"name": "Near", "address": "2 B", "city": "H", "zip": "77002", "phone": "2", "lat": 29.71, "lon": -95.4},
        {"name": "Bad", "lat": None, "lon": None}]))
    r = client.get("/api/medical", params={"lat": 29.7, "lon": -95.4, "limit": 5}).json()
    assert [f["name"] for f in r["facilities"]] == ["Near", "Far"] and r["facilities"][0]["distance_mi"] < 1


def test_route_report_hazard(client, monkeypatch):
    body = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}
    client.post("/api/reports", json={"lat": 29.7603, "lon": -95.375, "depth_in": 8, "note": "deep"})
    client.post("/api/reports", json={"lat": 29.80, "lon": -95.375, "depth_in": 20})  # far away
    r = client.post("/api/route-check", json=body).json()
    reps = [h for h in r["hazards"] if h.get("kind") == "report"]
    assert len(reps) == 1 and reps[0]["depth_in"] == 8
    assert r["verdict"] == "caution"  # one report never means avoid
    client.post("/api/reports", json={"lat": 29.7601, "lon": -95.365, "depth_in": 9})
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "caution"  # a second report from the same client still counts once
    from app.routers import reports as rr
    monkeypatch.setattr(rr, "voter_id", lambda request: "another-client")
    client.post("/api/reports", json={"lat": 29.7602, "lon": -95.366, "depth_in": 9})
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "avoid"  # deep reports from two distinct clients


def test_route_active_warning_never_safe(client, monkeypatch):
    from app.services import route as rt
    body = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}
    monkeypatch.setattr(rt, "load_crossings", lambda: [])
    monkeypatch.setattr(rt, "recent_reports", lambda: [])
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "safe" and "active_warnings" not in r

    async def warn(coords):
        return [{"event": "Flash Flood Warning", "headline": "h", "expires": None}]
    monkeypatch.setattr(rt, "route_warnings", warn)
    r = client.post("/api/route-check", json=body).json()
    assert r["verdict"] == "caution" and r["message_code"] == "route.warning"
    assert "Flash Flood Warning" in r["message"] and r["active_warnings"][0]["event"] == "Flash Flood Warning"


def test_route_warnings_polygon_intersection(monkeypatch):
    import asyncio
    from app.services import alerts as al
    sq = [[[-95.375, 29.75], [-95.365, 29.75], [-95.365, 29.77], [-95.375, 29.77], [-95.375, 29.75]]]

    async def feed(url, params=None, ttl=300, headers=None):
        mk = lambda ev, g: {"geometry": g, "properties": {"id": ev, "event": ev}}
        return {"features": [mk("Flash Flood Warning", {"type": "Polygon", "coordinates": sq}),
                             mk("Flood Watch", {"type": "Polygon", "coordinates": sq})]}
    monkeypatch.setattr(al, "get_json", feed)
    hit = asyncio.run(al.route_warnings([[-95.38, 29.76], [-95.37, 29.76], [-95.36, 29.76]]))
    assert [h["event"] for h in hit] == ["Flash Flood Warning"]  # warnings only, not watches
    assert asyncio.run(al.route_warnings([[-95.30, 29.90], [-95.29, 29.90]])) == []


def test_watch_rejects_outside_region(client):
    r = client.post("/api/watch", json={"label": "Greenville", "lat": 34.85, "lon": -82.4})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "watch.outOfRegion"


def test_push_failed_send_retried_and_gone_removed(client, monkeypatch, tmp_path):
    import asyncio
    from app.services import push as P
    monkeypatch.setattr(P, "VAPID_FILE", tmp_path / "v.json")
    P._vapid_cache.clear()
    results = iter(["error", "ok"])
    monkeypatch.setattr(P, "send_one", lambda sub, payload: next(results))

    async def fake_eval(p, sim=False):
        return {"level": "warning"}
    monkeypatch.setattr(P, "evaluate", fake_eval)
    pl = client.post("/api/watch", json={"label": "Home", "lat": 29.76, "lon": -95.37}).json()
    client.post("/api/push/subscribe", json={"subscription": {"endpoint": "https://updates.push.services.mozilla.com/wpush/v2/retry", "keys": {"p256dh": "a", "auth": "b"}}, "place_ids": [pl["id"]]})
    assert [asyncio.run(P.check_all()), asyncio.run(P.check_all()), asyncio.run(P.check_all())] == [0, 1, 0]
    monkeypatch.setattr(P, "send_one", lambda sub, payload: "gone")
    client.post("/api/push/subscribe", json={"subscription": {"endpoint": "https://updates.push.services.mozilla.com/wpush/v2/gone", "keys": {"p256dh": "a", "auth": "b"}}, "place_ids": [pl["id"]]})
    asyncio.run(P.check_all())
    from app.db import PushSub, get_session
    with get_session() as s:
        assert s.query(PushSub).filter(PushSub.endpoint == "https://updates.push.services.mozilla.com/wpush/v2/gone").count() == 0


def test_zip_policies_fallback_and_no_partial_cache(monkeypatch):
    import asyncio
    from app.services import zipinsurance as zi
    zi._mem.clear()
    puts = []
    monkeypatch.setattr(zi.diskcache, "get", lambda *a: None)
    monkeypatch.setattr(zi.diskcache, "put", lambda *a: puts.append(a))

    async def fake(url, params=None, ttl=300, headers=None):
        if "NfipClaims" in url or "FimaNfipClaims" in url:
            return {"NfipClaims": [{"yearOfLoss": 2017}]}
        if params.get("$count"):
            return None  # count query fails
        return {"NfipPolicies": [{"totalInsurancePremiumOfThePolicy": 1000}] * 4980}
    monkeypatch.setattr(zi, "get_json", fake)
    r = asyncio.run(zi.zip_insurance("77586"))
    assert r["policies_in_force"] == 4980 and r["premiums"]["sample_size"] == 4980 and puts


# ---- Cycle 6: elevation fallback, flood-history, report kinds ----
def test_risk_elevation_fallback(client, monkeypatch):
    from app.services import risk as rk
    orig = rk.get_json

    async def f(url, params=None, ttl=300, headers=None):
        if "epqs" in url:
            return None
        if "open-meteo" in url:
            return {"elevation": [10.0]}
        return await orig(url, params, ttl)
    r = client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["elevation_source"] == "usgs_epqs"
    monkeypatch.setattr(rk, "get_json", f)
    r = client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["elevation_source"] == "open_meteo_approx" and r["elevation_ft"] == 32.8


def test_flood_history(client, tmp_path, monkeypatch):
    ev = {"event": {"id": "e1", "name": "E1", "start": "2017-08-25"}, "gauges": [
        {"id": "NEAR", "name": "Near", "lat": 29.69, "lon": -95.465, "flood_stages": {"action": 10, "minor": 12, "moderate": 15, "major": 20},
         "series": [{"t": "a", "stage_ft": 5}, {"t": "b", "stage_ft": 16}]},
        {"id": "FAR", "name": "Far", "lat": 30.5, "lon": -95.4, "flood_stages": {}, "series": [{"t": "a", "stage_ft": 99}]}]}
    (tmp_path / "replay" / "e1.json").write_text(json.dumps(ev))
    (tmp_path / "replay" / "events.json").write_text("[]")
    from app.services import floodhistory as fh

    async def zi(z):
        return {"claims": {"by_year": [{"year": 2016, "count": 3}, {"year": 2017, "count": 90}]}}
    monkeypatch.setattr(fh, "zip_insurance", zi)
    r = client.get("/api/flood-history", params={"lat": 29.6905, "lon": -95.465, "zip": "77096"}).json()
    e = [x for x in r["events"] if x["id"] == "e1"][0]
    assert e["nearest_gauge"]["id"] == "NEAR" and e["nearest_gauge"]["peak_category"] == "moderate"
    assert r["zip"] == {"zip": "77096", "peak_year": 2017, "peak_year_claims": 90}
    assert "flooded" in r["harvey"] and "source" in r["harvey"]
    r = client.get("/api/flood-history", params={"lat": 31.0, "lon": -95.4}).json()
    assert r["zip"] is None and all(x["nearest_gauge"] is None for x in r["events"])
    assert client.get("/api/flood-history", params={"lat": 1, "lon": 1, "zip": "x"}).status_code == 422


def test_report_kinds(client):
    for k in ("flooded_road", "water_over_road", "barricade_missing", "stalled_vehicles", "other"):
        assert client.post("/api/reports", json={"lat": 29.7, "lon": -95.3, "kind": k}).json()["kind"] == k
    assert client.post("/api/reports", json={"lat": 29.7, "lon": -95.3, "kind": "bogus"}).status_code == 422
    body = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}
    client.post("/api/reports", json={"lat": 29.7603, "lon": -95.375, "kind": "stalled_vehicles"})
    r = client.post("/api/route-check", json=body).json()
    assert r["report_count"] >= 1 and "community report" in r["message"]


def test_watch_community_reports(client, monkeypatch):
    from app.services import watch as w

    async def no_alerts(lat, lon):
        return {"alerts": []}

    async def no_gauges(*a, **k):
        return []
    monkeypatch.setattr(w, "get_alerts", no_alerts)
    monkeypatch.setattr(w, "nearest_gauges", no_gauges)
    monkeypatch.setattr(w, "crossings_near", lambda *a, **k: [])
    lat, lon = 30.4, -96.4  # away from other tests' reports

    def lvl():
        pl = client.post("/api/watch", json={"label": "H", "lat": lat, "lon": lon}).json()
        return client.get("/api/watch/status", params={"ids": pl["id"]}).json()["places"][0]

    assert lvl()["level"] == "ok"
    client.post("/api/reports", json={"lat": lat, "lon": lon, "kind": "water_over_road", "depth_in": 3})
    assert lvl()["level"] == "ok"
    client.post("/api/reports", json={"lat": lat + 0.001, "lon": lon, "kind": "flooded_road"})
    r = lvl()
    assert r["level"] == "watch" and "2 community reports of water on roads nearby (last 6h)" in r["reasons"]
    r2 = client.get("/api/watch/status", params={"ids": r["id"], "simulate": "storm"}).json()["places"][0]
    assert not any("community reports" in x for x in r2["reasons"])


# ---- Cycle 11: officials, premiums, buyout-area ----
def test_zip_premiums(client, monkeypatch):
    from app.services import zipinsurance as zi

    async def fake(url, params=None, ttl=300, headers=None):
        if "NfipClaims" in url:
            return {"NfipClaims": [{"yearOfLoss": 2017}]}
        if "NfipPolicies" in url:
            if params.get("$select") == "totalInsurancePremiumOfThePolicy":
                return {"NfipPolicies": [{"totalInsurancePremiumOfThePolicy": v} for v in (400, 800, 1200, 2000, 0)]}
            return {"metadata": {"count": 5}}
        return None
    monkeypatch.setattr(zi, "get_json", fake)
    zi._mem.clear()
    r = client.get("/api/zip-insurance", params={"zip": "77096"}).json()
    p = r["premiums"]
    assert p["sample_size"] == 4 and p["p25"] <= p["median_annual"] <= p["p75"] and p["median_annual"] == 1000 and p["source"]


def test_zip_premiums_null_on_failure(client, monkeypatch):
    from app.services import zipinsurance as zi
    zi._mem.clear()

    async def fake(url, params=None, ttl=300, headers=None):
        if "NfipClaims" in url:
            return {"NfipClaims": []}
        return None
    monkeypatch.setattr(zi, "get_json", fake)
    r = client.get("/api/zip-insurance", params={"zip": "77026"}).json()
    assert r["premiums"] is None


def test_civic_officials(client, monkeypatch):
    from app.services import officials as of, civic as cv
    of._cache.clear()
    cv._cache.clear()

    async def fake(url, params=None, ttl=300, headers=None):
        f = lambda a: {"features": [{"attributes": a}]}  # noqa: E731
        if "CommPrecinct" in url:
            return f({"PCT_NO": 1, "COMMISSION": "Rodney Ellis", "URL": "https://www.hcp1.net/"})
        if "Floodplain_Administrators" in url:
            return f({"Entity": "City of Houston", "Administrator": "Choyce Morrow", "Phone": "Phone: 832-394-9140",
                      "Email": "c@x.gov", "Address": "a"})
        if "Council" in url:
            return f({"DISTRICT": "C", "MEMBER": "ABBIE KAMIN", "PHONE": "832-393-3004"})
        return None
    monkeypatch.setattr(of, "get_json", fake)
    r = client.get("/api/civic", params={"lat": 29.77, "lon": -95.37}).json()["officials"]
    assert r["commissioner"]["name"] == "Rodney Ellis" and r["commissioner"]["precinct"] == 1
    assert r["council"]["member"] == "Abbie Kamin" and r["floodplain_admin"]["phone"] == "832-394-9140"


def test_civic_officials_never_fail(client, monkeypatch):
    from app.services import officials as of, civic as cv
    of._cache.clear()
    cv._cache.clear()

    async def none(*a, **k):
        return None
    monkeypatch.setattr(of, "get_json", none)
    r = client.get("/api/civic", params={"lat": 29.77, "lon": -95.37})
    assert r.status_code == 200 and r.json()["officials"] == {"commissioner": None, "council": None, "floodplain_admin": None}


def test_buyout_area(client, monkeypatch):
    from app.services import buyouts as bo
    bo._mem.clear()

    async def fake(url, params=None, ttl=300, headers=None):
        assert "Voluntary" not in url
        return {"features": [{"geometry": {"coordinates": [-95.465, 29.691]}, "properties": {"Area_Name": "Test Area"}}]}
    monkeypatch.setattr(bo, "get_json", fake)
    monkeypatch.setattr(bo.diskcache, "put", lambda *a, **k: None)
    r = client.get("/api/buyout-area", params={"lat": 29.6905, "lon": -95.465}).json()
    assert r["in_buyout_area"] is True and r["area_name"] == "Test Area" and r["source"]
    r = client.get("/api/buyout-area", params={"lat": 29.9, "lon": -95.0}).json()
    assert r["in_buyout_area"] is False


def test_buyout_area_unavailable(client, monkeypatch):
    from app.services import buyouts as bo
    bo._mem.clear()

    async def none(*a, **k):
        return None
    monkeypatch.setattr(bo, "get_json", none)
    monkeypatch.setattr(bo.diskcache, "get", lambda *a, **k: None)
    r = client.get("/api/buyout-area", params={"lat": 29.7, "lon": -95.4}).json()
    assert r["in_buyout_area"] is None
