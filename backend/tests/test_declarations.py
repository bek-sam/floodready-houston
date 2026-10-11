from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.services import declarations as dec


def _client():
    from app.main import app
    return TestClient(app)


def _row(n, d, end, ia, ih):
    return {"disasterNumber": n, "declarationTitle": f"T{n}", "declarationDate": d + "T00:00:00.000Z",
            "incidentType": "Flood", "incidentBeginDate": d + "T00:00:00.000Z",
            "incidentEndDate": (end + "T00:00:00.000Z") if end else None,
            "iaProgramDeclared": ia, "ihProgramDeclared": ih}


def test_active(monkeypatch):
    recent = (date.today() - timedelta(days=10)).isoformat()
    async def fake(url, params=None, ttl=300, headers=None):
        assert "Harris (County)" in params["$filter"] and ttl == 6 * 3600
        return {"DisasterDeclarationsSummaries": [_row(5000, recent, None, True, True), _row(4798, "2024-07-09", "2024-07-20", False, True)]}
    monkeypatch.setattr(dec, "get_json", fake)
    d = _client().get("/api/declarations?county=Harris&state=TX").json()
    assert d["available"] and d["active_ia"] and d["latest"]["disaster_number"] == 5000
    assert d["latest"]["url"] == "https://www.fema.gov/disaster/5000" and len(d["recent"]) == 2
    assert d["meta"]["freshness"] == "live"


def test_inactive_old(monkeypatch):
    async def fake(url, params=None, ttl=300, headers=None):
        return {"DisasterDeclarationsSummaries": [_row(4798, "2024-07-09", "2024-07-20", False, True)]}
    monkeypatch.setattr(dec, "get_json", fake)
    d = _client().get("/api/declarations").json()
    assert d["available"] and not d["active_ia"] and d["latest"]["ha_program"] and not d["latest"]["ia_program"]


def test_failure(monkeypatch):
    async def fake(*a, **k):
        return None
    monkeypatch.setattr(dec, "get_json", fake)
    r = _client().get("/api/declarations")
    d = r.json()
    assert r.status_code == 200 and d["available"] is False and d["warnings"] and d["latest"] is None and "meta" in d
