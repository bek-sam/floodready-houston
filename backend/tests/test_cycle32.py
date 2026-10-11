import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import ratelimit
from app.main import app
from app.services import alerts, rain24

client = TestClient(app)


def test_build_past_sums():
    now = datetime(2026, 10, 11, 12, 30, tzinfo=timezone.utc)
    start = datetime(2026, 10, 8, 12, 0)
    times = [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(96)]
    vals = [0.01] * 96
    vals[30] = 0.5
    p = rain24.build_past({"time": times, "precipitation": vals}, now)
    assert p["available"] and p["last72_in"] == 1.21 and p["last24_in"] == 0.24
    assert p["peak_hour"]["in"] == 0.5


def test_past_failure(monkeypatch):
    async def none(*a, **k):
        return None
    monkeypatch.setattr(rain24, "get_json", none)
    out = asyncio.run(rain24.get_rain24(29.76, -95.37))
    assert out["available"] is False and out["past"]["available"] is False


def test_area_alerts(monkeypatch):
    poly = {"type": "Polygon", "coordinates": [[[-95.5, 29.5], [-95.0, 29.5], [-95.0, 30.0], [-95.5, 29.5]]]}
    far = {"type": "Polygon", "coordinates": [[[-100, 35], [-99, 35], [-99, 36], [-100, 35]]]}
    feats = [
        {"geometry": poly, "properties": {"id": "a1", "event": "Flash Flood Warning", "headline": "h"}},
        {"geometry": far, "properties": {"id": "a2", "event": "Flood Warning"}},
        {"geometry": None, "properties": {"id": "a3", "event": "Coastal Flood Advisory", "areaDesc": "Galveston"}},
        {"geometry": poly, "properties": {"id": "a4", "event": "Heat Advisory"}},
    ]

    async def fake(*a, **k):
        return {"features": feats}
    monkeypatch.setattr(alerts, "get_json", fake)
    r = client.get("/api/alerts/area?bbox=-96.5,29,-94.5,30.5").json()
    assert [f["properties"]["id"] for f in r["features"]] == ["a1"]
    assert r["features"][0]["properties"]["source"].endswith("/a1")
    assert r["zone_only"][0]["area_desc"] == "Galveston" and r["meta"]["freshness"] == "live"

    async def bad(*a, **k):
        return None
    monkeypatch.setattr(alerts, "get_json", bad)
    r = client.get("/api/alerts/area").json()
    assert r["features"] == [] and r["meta"]["freshness"] == "cached"


def test_votes_and_filter():
    ratelimit.reset()
    r = client.post("/api/reports", json={"lat": 29.7, "lon": -95.4, "kind": "flooded_road", "depth_in": 8}).json()
    rid = r["id"]
    assert r["confirms"] == 0
    assert client.post("/api/reports/nope/vote", json={"still_there": True}).status_code == 404
    v = client.post(f"/api/reports/{rid}/vote", json={"still_there": False}).json()
    assert v["clears"] == 1 and not v["cleared"]
    v = client.post(f"/api/reports/{rid}/vote", json={"still_there": False}).json()
    assert v["clears"] == 2 and v["cleared"]
    item = next(x for x in client.get("/api/reports").json() if x["id"] == rid)
    assert item["clears"] == 2 and item["confirms"] == 0
    from app.services.route import recent_reports
    assert rid not in [x["id"] for x in recent_reports()]
    client.post(f"/api/reports/{rid}/vote", json={"still_there": True})
    client.post(f"/api/reports/{rid}/vote", json={"still_there": True})
    client.post(f"/api/reports/{rid}/vote", json={"still_there": True})
    assert rid in [x["id"] for x in recent_reports()]


def test_age_filter_and_rate_limit():
    ratelimit.reset()
    from app.db import Report, get_session
    with get_session() as s:
        s.add(Report(lat=29.7, lon=-95.4, kind="other", note="old",
                     created_at=datetime.now(timezone.utc) - timedelta(hours=10)))
        s.commit()
    assert "old" not in [x["note"] for x in client.get("/api/reports").json()]
    assert "old" in [x["note"] for x in client.get("/api/reports?since_hours=24").json()]
    codes = [client.post("/api/reports", json={"lat": 29.7, "lon": -95.4}).status_code for _ in range(25)]
    assert 429 in codes
    ratelimit.reset()
