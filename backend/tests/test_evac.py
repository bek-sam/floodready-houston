from tests.test_api import client  # noqa: F401  (shared app fixture)
import pytest

from app.services import evac as evac_mod

SEABROOK = (29.564, -95.025)


def _fake(zone_feats, classes, fail=False):
    async def fake(url, params=None, ttl=300, headers=None):
        if fail:
            return None
        if "HurricaneEvac" in url:
            return {"features": [{"attributes": a} for a in zone_feats]}
        layer = int(params["layers"].split(":")[1])
        cn = classes.get(layer)
        return {"results": [{"attributes": {"Raster.ClassName": cn}}] if cn else []}
    return fake


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    evac_mod._mem.clear()
    monkeypatch.setattr(evac_mod.diskcache, "put", lambda *a, **k: None)
    monkeypatch.setattr(evac_mod.diskcache, "get", lambda *a, **k: None)


def test_seabrook(client, monkeypatch):
    monkeypatch.setattr(evac_mod, "get_json", _fake(
        [{"Zone": "Zip-Zone A", "Zip5digit": "77586", "Name": "SEABROOK", "County": "HARRIS"}],
        {9: "Less than 3 feet above ground", 13: "Greater than 6 feet above ground"}))
    r = client.get("/api/evac", params={"lat": 29.564, "lon": -95.025}).json()
    assert r["zone"] == "A" and r["zip"] == "77586"
    assert r["surge"]["cat1"] is None and r["surge"]["cat3"].startswith("Greater than 6")
    assert r["zone_status"] == "in_zone" and r["surge_ranges"]["cat3"] == {"min_ft": 6, "max_ft": None, "label": "6+ ft"}
    assert r["surge_status"] == "mapped" and "official" in r["guidance"].lower()
    assert r["meta"]["freshness"] == "live"


def test_outside_coverage_is_null_with_note(client, monkeypatch):
    monkeypatch.setattr(evac_mod, "get_json", _fake([], {}))
    r = client.get("/api/evac", params={"lat": 29.6876, "lon": -95.4583}).json()
    assert r["zone"] is None and r["zone_status"] == "not_in_zone" and r["surge_status"] == "none"
    assert all(v is None for v in r["surge"].values()) and r["notes"]


def test_failure_never_reads_safe(client, monkeypatch):
    monkeypatch.setattr(evac_mod, "get_json", _fake([], {}, fail=True))
    r = client.get("/api/evac", params={"lat": 30.05, "lon": -95.19}).json()
    assert r["zone"] is None and r["zone_status"] == "unavailable" and r["surge_status"] == "unavailable"
    assert r["meta"]["freshness"] == "stale"
