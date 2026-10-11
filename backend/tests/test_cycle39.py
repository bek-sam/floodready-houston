import json

from tests.test_api import client  # noqa: F401  (fixture, network mocked)
from app.services import http as http_mod

LINE = lambda y: {"type": "LineString", "coordinates": [[-95.38, y], [-95.37, y], [-95.36, y]]}  # noqa: E731
BODY = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}


def _osrm(monkeypatch, routes):
    import app.services.route as rt
    orig = rt.get_json

    async def fake(url, params=None, ttl=300, headers=None):
        if "osrm" in url:
            assert params.get("alternatives") == "true"
            return {"routes": routes}
        return await orig(url, params, ttl, headers)
    monkeypatch.setattr(rt, "get_json", fake)


def test_route_alternative_fewer_hazards(client, monkeypatch):
    _osrm(monkeypatch, [{"geometry": LINE(29.76), "duration": 600, "distance": 8000},
                        {"geometry": LINE(29.70), "duration": 780, "distance": 9609.344}])
    r = client.post("/api/route-check?simulate=storm", json=BODY).json()
    assert r["verdict"] == "avoid"
    a = r["alternative"]
    assert a["hazard_count"] == 0 and a["hazards"] == [] and a["extra_min"] == 3.0 and a["extra_mi"] == 1.0
    assert a["route"]["type"] == "LineString" and a["message_code"] == "route.alt"
    assert "safe" not in a["message"].lower().split("no known")[0]


def test_route_alternative_omitted(client, monkeypatch):
    # alternative passes the same crossing -> not strictly fewer -> omitted
    _osrm(monkeypatch, [{"geometry": LINE(29.76), "duration": 600, "distance": 8000},
                        {"geometry": LINE(29.76), "duration": 700, "distance": 9000}])
    r = client.post("/api/route-check?simulate=storm", json=BODY).json()
    assert r["verdict"] == "avoid" and "alternative" not in r


def test_medical_exposure(client, tmp_path):
    (tmp_path / "dialysis.json").write_text(json.dumps([{"name": "D1", "lat": 29.76, "lon": -95.37, "address": "1 A", "city": "H", "zip": "77001"}]))
    f = client.get("/api/medical", params={"lat": 29.76, "lon": -95.37}).json()["facilities"][0]
    assert f["fema_zone"] == "X" and f["sfha"] is False and "harvey_flooded" in f


def test_medical_exposure_failure_null(client, tmp_path, monkeypatch):
    (tmp_path / "dialysis.json").write_text(json.dumps([{"name": "D1", "lat": 29.76, "lon": -95.37}]))
    import app.services.risk as risk

    async def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(risk, "_fema", boom)
    r = client.get("/api/medical", params={"lat": 29.76, "lon": -95.37})
    f = r.json()["facilities"][0]
    assert r.status_code == 200 and f["fema_zone"] is None and f["sfha"] is None
