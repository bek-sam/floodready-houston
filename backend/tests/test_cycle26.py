import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services import gauges, nri, outlook

client = TestClient(app)


def test_insurance_exceptions():
    d = client.get("/api/insurance/countdown?purchase_date=2026-10-11").json()
    assert d["days_wait"] == 30 and d["exceptions_note_code"] == "ins.exceptions"
    assert "Exceptions exist" in d["exceptions_note"] and "generally" in d["message"]


def _layers(monkeypatch, fail=()):
    async def fake(url, params=None, ttl=0, **k):
        n = int(url.split("/")[-2])
        if n in fail:
            return None
        cat = {0: "Slight Risk", 1: "Marginal Risk"}.get(n)
        feats = [{"attributes": {"outlook": cat, "valid_time": "t%d" % n}}] if cat else []
        return {"features": feats}
    monkeypatch.setattr(outlook, "get_json", fake)


def test_outlook_days(monkeypatch):
    _layers(monkeypatch)
    o = asyncio.run(outlook.get_outlook(29.7, -95.4))
    assert len(o["days"]) == 5 and o["day1"]["category"] == "Slight"
    assert o["max_category"] == "Slight" and o["prepare_nudge"] is True
    assert o["days"][2]["category"] == "None"


def test_outlook_partial_and_sim(monkeypatch):
    _layers(monkeypatch, fail=(2,))
    o = asyncio.run(outlook.get_outlook(29.7, -95.4))
    assert o["days"][2]["category"] is None and o["warnings"]
    s = asyncio.run(outlook.get_outlook(29.7, -95.4, True))
    assert s["prepare_nudge"] and s["days"][1]["category"] == "Moderate" and s["day1"]["category"] == "Slight"


def test_nri(monkeypatch):
    async def ok(url, params=None, ttl=0, **k):
        assert "RFLD" not in params["outFields"]
        return {"features": [{"attributes": {"TRACTFIPS": "48201420800", "IFLD_RISKR": "Very High", "POPULATION": 2274}}]}
    monkeypatch.setattr(nri, "get_json", ok)
    r = client.get("/api/nri?lat=29.687&lon=-95.4698").json()
    assert r["tract"] == "48201420800" and r["inland_flood"]["rating"] == "Very High" and "meta" in r

    async def empty(*a, **k):
        return {"features": []}
    monkeypatch.setattr(nri, "get_json", empty)
    assert client.get("/api/nri?lat=0&lon=0").json()["available"] is False

    async def none(*a, **k):
        return None
    monkeypatch.setattr(nri, "get_json", none)
    assert client.get("/api/nri?lat=0&lon=0").json()["available"] is False


def test_gauge_impact(monkeypatch):
    monkeypatch.setattr(gauges, "_impacts", {"G1": {"impacts": [{"stage": 10, "statement": "a"}, {"stage": 20, "statement": "b"}],
                                                    "harvey_crest": {"stage": 30.0}, "source": "http://x"}, "G2": {"impacts": []}})
    i = gauges._impact_for("G1", 12)
    assert i["current"]["stage"] == 10 and i["next"]["stage"] == 20 and i["harvey_delta_ft"] == 18.0
    assert gauges._impact_for("G1", None)["current"] is None
    assert gauges._impact_for("G2", 5)["current"] is None
    assert gauges._impact_for("NOPE", 5) is None
    monkeypatch.setattr(gauges, "_impacts", {})
    assert gauges._impact_for("G1", 5) is None
