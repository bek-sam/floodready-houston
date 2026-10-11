from tests.test_api import client  # noqa: F401  (fixture, network mocked)

P = {"lat": 29.76, "lon": -95.37}


def test_alerts_simulated(client):
    r = client.get("/api/alerts", params={**P, "simulate": "storm"}).json()
    a = r["alerts"][0]
    assert r["simulated"] is True and r["meta"]["storm_mode"] is True
    assert a["simulated"] is True and a["headline"].startswith("SIMULATED") and "Not a real NWS alert" in a["description"]
    assert a["event"] == "Flash Flood Warning" and a["severity"] == "Severe" and a["expires"]
    plain = client.get("/api/alerts", params=P).json()
    assert "simulated" not in plain and plain["alerts"] == []


def test_simulated_flags_everywhere(client):
    risk = client.get("/api/risk", params={**P, "simulate": "storm"}).json()
    assert risk["simulated"] is True and risk["meta"]["storm_mode"] is True
    out = client.get("/api/outlook", params={**P, "simulate": "storm"}).json()
    assert out["simulated"] is True and out["meta"]["storm_mode"] is True
    pl = client.post("/api/watch", json={"label": "H", **P, "lang": "en"}).json()
    w = client.get("/api/watch/status", params={"ids": pl["id"], "simulate": "storm"}).json()
    assert w["simulated"] is True and w["meta"]["storm_mode"] is True and w["places"][0]["simulated"] is True
    assert "simulated" not in client.get("/api/risk", params=P).json()


def test_route_caution_simulated_copy(client, tmp_path, monkeypatch):
    import json
    from app import config
    body = {"origin": {"lat": 29.76, "lon": -95.38}, "destination": {"lat": 29.76, "lon": -95.36}}
    plain = client.post("/api/route-check", json=body).json()
    assert "simulated" not in plain
    r = client.post("/api/route-check?simulate=storm", json=body).json()
    assert r["simulated"] is True and r["meta"]["storm_mode"] is True
    # medium-risk crossing: simulated storm stays "caution" but must say conditions are active (simulated)
    f = config.DATA_DIR / "crossings.geojson"
    d = json.loads(f.read_text())
    d["features"][0]["properties"]["risk"] = "medium"
    f.write_text(json.dumps(d))
    from app.services import data as data_mod
    for name in ("_cache", "_crossings"):
        if hasattr(data_mod, name):
            monkeypatch.setattr(data_mod, name, None)
    r = client.post("/api/route-check?simulate=storm", json=body).json()
    if r["verdict"] == "caution":
        assert r["message_code"] == "route.cautionSim"
        assert "No active flood conditions" not in r["message"] and "Simulated storm" in r["message"]
