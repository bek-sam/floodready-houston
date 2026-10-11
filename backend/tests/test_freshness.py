from datetime import datetime, timedelta, timezone

from app import freshness
from app.routers import status as status_router
from tests.test_api import client  # noqa: F401  (fixture)


def _iso(**kw):
    return (datetime.now(timezone.utc) - timedelta(**kw)).isoformat()


def test_gauge_flags_stale_provisional_spike():
    t = datetime.now(timezone.utc)
    f = freshness.gauge_flags((t - timedelta(hours=3)).isoformat())
    assert f["stale"] and f["provisional"] and not f["spike"]
    f = freshness.gauge_flags(t.isoformat(), [(t - timedelta(minutes=10), 4.0), (t, 8.5)])
    assert f["spike"] and not f["stale"]
    f = freshness.gauge_flags(t.isoformat(), [(t - timedelta(hours=2), 4.0), (t, 8.5)])
    assert not f["spike"]
    assert freshness.gauge_flags((t - timedelta(days=200)).isoformat())["provisional"] is False
    assert freshness.gauge_flags(t.isoformat(), approval="Approved")["provisional"] is False


def test_storm_ttl_and_circuit():
    freshness.clear_storm()
    assert freshness.effective_ttl("https://api.weather.gov/x", 3600) == 3600
    freshness.mark_storm()
    assert freshness.effective_ttl("https://api.weather.gov/x", 3600) == freshness.STORM_TTL
    assert freshness.effective_ttl("https://example.com/x", 3600) == 3600
    freshness.clear_storm()
    freshness.reset_health()
    for _ in range(5):
        freshness.record("NWS", False, 0, "Timeout")
    assert freshness.health("NWS")["circuit"] == "open"
    freshness.record("NWS", True, 120)
    h = freshness.health("NWS")
    assert h["circuit"] == "closed" and h["p50_ms"] == 120 and h["last_success"]


def test_endpoints_carry_meta(client):  # noqa: F811
    freshness.clear_storm()
    a = client.get("/api/alerts", params={"lat": 1, "lon": 2}).json()
    assert a["meta"]["freshness"] == "live" and a["meta"]["storm_mode"] is False and a["meta"]["as_of"]
    r = client.get("/api/risk", params={"lat": 29.76, "lon": -95.37}).json()
    assert r["meta"]["freshness"] == "live"
    g = r["nearest_gauges"][0]
    assert {"stale", "provisional", "spike", "offline"} <= set(g)
    c = client.get("/api/crossings").json()
    assert c["meta"]["freshness"] == "snapshot" and "snapshot_date" in c["meta"]
    s = client.get("/api/shelters", params={"lat": 29.7, "lon": -95.3}).json()
    assert s["meta"]["freshness"] == "historical"


def test_storm_mode_from_flood_alert(client, monkeypatch):  # noqa: F811
    import app.services.alerts as al

    async def fake(url, params=None, ttl=300, headers=None):
        return {"features": [{"properties": {"event": "Flash Flood Warning", "severity": "Severe"}}]}
    monkeypatch.setattr(al, "get_json", fake)
    freshness.clear_storm()
    a = client.get("/api/alerts", params={"lat": 1, "lon": 2}).json()
    assert a["meta"]["storm_mode"] is True and freshness.storm_on()
    freshness.clear_storm()


def test_status_endpoint(client, monkeypatch):  # noqa: F811
    async def noprobe():
        return None
    monkeypatch.setattr(status_router, "probe_all", noprobe)
    status_router._cache.update(t=0.0, data=None)
    r = client.get("/api/status").json()
    names = {s["name"] for s in r["sources"]}
    assert {"NWS", "USGS OGC", "NOAA NWPS", "FEMA NFHL", "OSRM", "DB", "Gemini", "ElevenLabs"} <= names
    assert all("circuit" in s for s in r["sources"])
    assert {"crossings", "harvey", "dialysis", "shelters", "knowledge"} <= set(r["snapshots"])
