from fastapi.testclient import TestClient

from app.services import coastal as co
from app.services import hwm


class _Lazy:
    def get(self, *a, **k):
        from app.main import app
        return TestClient(app).get(*a, **k)


c = _Lazy()


def test_hwm_snapshot_nearest(monkeypatch):
    monkeypatch.setattr(hwm, "_snap", {"snapshot_date": "2026-10-11", "marks": [
        {"id": 1, "lat": 29.70, "lon": -95.40, "h": 3.2, "elev": 40, "q": "Good", "desc": "Brays", "date": "2017-09-10"},
        {"id": 2, "lat": 29.71, "lon": -95.40, "h": 0.0, "elev": 41, "q": "Good", "desc": "Far", "date": "2017-09-10"},
        {"id": 3, "lat": 31.0, "lon": -95.40, "h": 9.0, "elev": 1, "q": "Good", "desc": "Out", "date": "2017-09-10"}]})
    d = c.get("/api/hwm", params={"lat": 29.704, "lon": -95.40}).json()
    assert [m["id"] for m in d["marks"]] == [1, 2]
    assert d["nearest_depth_ft"] == 3.2
    assert "above ground at a surveyed point" in d["marks"][0]["note"] and "not your exact address" in d["marks"][0]["note"]
    assert "does not mean your address stayed dry" in d["marks"][1]["note"]
    assert d["meta"]["freshness"] == "historical" and d["meta"]["snapshot_date"] == "2026-10-11"


def test_hwm_none_nearby_and_validation():
    d = c.get("/api/hwm", params={"lat": 45.0, "lon": -100.0}).json()
    assert d["marks"] == [] and d["nearest_depth_ft"] is None and "No surveyed" in d["nearest_note"]
    assert c.get("/api/hwm", params={"lat": 99, "lon": 0}).status_code == 422


def test_hwm_real_snapshot_has_marks():
    hwm._snap.clear()
    d = hwm.nearby(29.62, -95.45, 10)
    assert d["marks"] and d["marks"][0]["distance_mi"] <= 10


def _mock(monkeypatch, obs, pred, nhc):
    async def fake(url, params=None, ttl=300, headers=None):
        if "CurrentStorms" in url:
            return nhc
        return obs if params["product"] == "water_level" else pred
    monkeypatch.setattr(co, "get_json", fake)


def test_coastal_normal(monkeypatch):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    hr = now
    _mock(monkeypatch, {"data": [{"t": now, "v": "3.0"}]}, {"predictions": [{"t": hr, "v": "2.6"}]},
          {"activeStorms": [{"id": "al092026", "name": "Isaias", "classification": "PTC", "latitudeNumeric": 25,
                             "longitudeNumeric": -90, "publicAdvisory": {"url": "https://nhc/x"}},
                            {"id": "ep012026", "name": "Pacific", "classification": "TS"}]})
    d = c.get("/api/coastal").json()
    assert d["tide"]["anomaly_ft"] == 0.4 and d["tide"]["stale"] is False
    assert [s["name"] for s in d["active_storms"]] == ["Isaias"] and d["active_storms"][0]["gulf_of_mexico"]
    assert d["meta"]["freshness"] == "live"


def test_coastal_missing_and_stale(monkeypatch):
    _mock(monkeypatch, None, None, None)
    d = c.get("/api/coastal").json()
    assert d["tide"]["observed_ft"] is None and d["tide"]["anomaly_ft"] is None
    assert d["tide"]["note"] == "Unavailable" and d["active_storms"] == [] and d["meta"]["freshness"] == "unavailable"
    _mock(monkeypatch, {"data": [{"t": "2020-01-01 00:00", "v": "3.0"}]}, {"predictions": [{"t": "2020-01-01 00:00", "v": "2.0"}]}, {})
    d = c.get("/api/coastal").json()
    assert d["tide"]["stale"] is True and d["meta"]["freshness"] == "stale"
