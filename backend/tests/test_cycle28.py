import asyncio

from app.services import airports, reservoir, zipinsurance

NWPS = {"status": {"observed": {"primary": 83.89, "validTime": "2026-10-11T10:15:00Z"}},
        "flood": {"categories": {"action": {"stage": 93}, "minor": {"stage": 96}}}}


def _patch(mp, nwps, elev, in_area=True):
    async def gj(url, params=None, ttl=300, headers=None):
        return nwps

    async def el(lat, lon):
        return elev

    async def rs(lat, lon):
        return {"in_area": in_area}
    mp.setattr(reservoir, "get_json", gj)
    mp.setattr(reservoir.risk_svc, "_elev", el)
    mp.setattr(reservoir.risk_svc, "reservoir_status", rs)


def test_pool_normal(monkeypatch):
    _patch(monkeypatch, NWPS, {"value": 95.0})
    r = asyncio.run(reservoir.get_pool(29.79, -95.62))
    assert r["available"] and r["pool"]["status"] == "normal"
    assert r["pool_below_ground_ft"] == 11.1 and r["harvey_above_ground_ft"] == 14.1
    assert r["relevant"] and r["message_code"] == "res.pool.below" and r["barker"] is None


def test_pool_no_elevation(monkeypatch):
    _patch(monkeypatch, NWPS, None)
    r = asyncio.run(reservoir.get_pool(29.79, -95.62))
    assert r["available"] and r["pool_below_ground_ft"] is None and not r["relevant"]


def test_pool_upstream_fail(monkeypatch):
    _patch(monkeypatch, None, {"value": 95.0})
    r = asyncio.run(reservoir.get_pool(29.79, -95.62))
    assert r["available"] is False and r["pool"] is None and r["meta"]["freshness"] == "snapshot"


def test_airports_parse():
    xml = ("<X><Airport><ARPT>IAH</ARPT><Reason>r</Reason><Reopen>soon</Reopen></Airport>"
           "<Airport><ARPT>SAN</ARPT></Airport></X>")
    a = {x["code"]: x for x in airports.parse(xml)}
    assert a["IAH"]["closed"] and a["IAH"]["reopen"] == "soon" and a["HOU"]["closed"] is False


def test_zip_transient_policy_failure_not_cached_24h(monkeypatch):
    zipinsurance._mem.clear()
    calls = {"n": 0}

    async def claims(z):
        return [2018, 2019]

    async def none(z):
        calls["n"] += 1
        return None
    monkeypatch.setattr(zipinsurance, "_claims", claims)
    monkeypatch.setattr(zipinsurance, "_policies", none)
    monkeypatch.setattr(zipinsurance, "_premiums", none)
    monkeypatch.setattr(zipinsurance.diskcache, "get", lambda *a: None)
    puts = []
    monkeypatch.setattr(zipinsurance.diskcache, "put", lambda *a: puts.append(a))
    r = asyncio.run(zipinsurance.zip_insurance("77096"))
    assert r["warnings"] and r["premiums"] is None and not puts
    entry = zipinsurance._mem["77096"]
    assert zipinsurance.time.time() - entry["fetched_at"] > zipinsurance.TTL - 400
    zipinsurance._mem.clear()


def test_premiums_truncated_flag(monkeypatch):
    async def gj(url, params=None, ttl=0, headers=None):
        return {"NfipPolicies": [{"totalInsurancePremiumOfThePolicy": 500}] * 10000}
    monkeypatch.setattr(zipinsurance, "get_json", gj)
    p = asyncio.run(zipinsurance._premiums("77096"))
    assert p["truncated"] is True and p["sample_size"] == 10000
