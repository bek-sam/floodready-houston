from tests.test_api import client  # noqa: F401
from app.services import empower as em, civic as civic_mod


def test_empower_ok(client, monkeypatch):
    async def fake(url, params=None, ttl=300, headers=None):
        assert params["where"] == "Zip_Code='77096'" and ttl == 7 * 24 * 3600
        return {"features": [{"attributes": {"Medicare_Benes": 5000, "Power_Dependent_Devices_DME": 900,
                                             "O2_Services_Any_DME": 400, "Facility_ESRD_Dialysis_Any_DME": 30}}]}
    monkeypatch.setattr(em, "get_json", fake)
    j = client.get("/api/empower?zip=77096").json()
    assert j["available"] and j["medicare_benes"] == 5000 and j["oxygen"] == 400 and j["dialysis"] == 30
    assert j["puc"]["url"] and j["co"]["url"] and j["meta"]["source"]


def test_empower_failure_and_validation(client, monkeypatch):
    async def fake(*a, **k):
        return None
    monkeypatch.setattr(em, "get_json", fake)
    r = client.get("/api/empower?zip=77096")
    assert r.status_code == 200
    j = r.json()
    assert j["available"] is False and j["medicare_benes"] is None and j["puc"] and j["note"]
    assert client.get("/api/empower?zip=abc").status_code == 422
    assert client.get("/api/empower?zip=77096'%20OR%201=1").status_code == 422


def test_civic_explicit_codes(client, monkeypatch):
    monkeypatch.setattr(civic_mod, "load_json", lambda *a, **k: {
        "bond": {"facts": [{"text": "a", "code": "civic.bond.4"}, {"text": "b"}]},
        "reservoir": {"facts": [{"text": "c", "code": "civic.res.3"}, {"text": "d"}]}})
    async def none(*a, **k):
        return []
    monkeypatch.setattr(civic_mod, "bond_projects", none)
    import asyncio
    d = asyncio.run(civic_mod.get_civic(29.76, -95.37))
    assert [f["code"] for f in d["bond"]["facts"]] == ["civic.bond.4", "civic.bond.1"]
    assert [f["code"] for f in d["reservoir"]["facts"]] == ["civic.res.3", "civic.res.1"]
