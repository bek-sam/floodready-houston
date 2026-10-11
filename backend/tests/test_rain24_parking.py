from datetime import datetime, timedelta, timezone

import asyncio

from app.services import parking, rain24

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def _grid(vals):
    return {"properties": {"updateTime": "2026-10-11T10:00:00+00:00",
                           "quantitativePrecipitation": {"uom": "wmoUnit:mm", "values": [
                               {"validTime": f"{(NOW + timedelta(hours=6 * i)).isoformat()}/PT6H", "value": v}
                               for i, v in enumerate(vals)]}}}


def _hourly(pops):
    return {"properties": {"periods": [
        {"startTime": (NOW + timedelta(hours=i)).isoformat(), "endTime": (NOW + timedelta(hours=i + 1)).isoformat(),
         "probabilityOfPrecipitation": {"value": p}, "shortForecast": "Rain"} for i, p in enumerate(pops)]}}


def test_parse_qpf_converts_and_limits():
    w = rain24.parse_qpf(_grid([25.4, 0, 12.7, 0, 50.8, 99]), NOW)
    assert [x["inches"] for x in w] == [1.0, 0.0, 0.5, 0.0]


def test_build_wettest_and_action():
    qpf = rain24.parse_qpf(_grid([0, 30, 5, 0]), NOW)
    out = rain24.build(qpf, rain24.parse_pop(_hourly([10] * 24), NOW))
    assert out["total_inches"] == round(35 / 25.4, 2)
    assert out["wettest_window"]["inches"] == round(30 / 25.4, 2)
    assert out["action"]["show"] and "safe" in out["action"]["text"]  # only in a negation
    dry = rain24.build(rain24.parse_qpf(_grid([0, 0, 0, 0]), NOW), rain24.parse_pop(_hourly([5] * 24), NOW))
    assert dry["wettest_window"] is None and not dry["action"]["show"]


def test_pop_trigger():
    out = rain24.build([], rain24.parse_pop(_hourly([10, 70] + [0] * 22), NOW))
    assert out["max_pop_pct"] == 70 and out["action"]["show"]


def test_unavailable(monkeypatch):
    async def none(*a, **k):
        return None
    monkeypatch.setattr(rain24, "get_json", none)
    out = asyncio.run(rain24.get_rain24(29.7, -95.4))
    assert out["available"] is False and out["total_inches"] is None and out["windows"] == []
    assert out["meta"]["source"]


def test_verdict_wording():
    assert parking.verdict_for([{"code": "x"}], False)["level"] == "move"
    v = parking.verdict_for([], False)
    assert v["level"] == "no_flags" and "not mean" in v["detail"]
    assert " safe" not in v["headline"].lower()


def test_codes():
    v = parking.verdict_for([{"code": "x"}], False)
    assert v["headline_code"] == "p30.park.move.h" and v["detail_code"] == "p30.park.move.d"
    v = parking.verdict_for([], False)
    assert v["headline_code"] == "p30.park.ok.h" and v["detail_code"] == "p30.park.ok.d"


def test_parking_reservoir_pool(monkeypatch):
    from app.services import reservoir
    base = {"fema_zone": "X", "sfha": False, "harvey": {"flooded": False}, "reservoir_area": True, "elevation_ft": 92.0}

    async def risk(lat, lon):
        return base

    async def alerts(lat, lon):
        return {"alerts": []}

    async def hg(*a, **k):
        return None
    monkeypatch.setattr(parking, "get_risk", risk)
    monkeypatch.setattr(parking, "get_alerts", alerts)
    monkeypatch.setattr(parking, "higher_ground", hg)

    async def pool_ok(lat, lon):
        return {"pool": {"status": "normal", "stage_ft": 80}}

    async def pool_hi(lat, lon):
        return {"pool": {"status": "action", "stage_ft": 94}}
    monkeypatch.setattr(reservoir, "get_pool", pool_ok)
    out = asyncio.run(parking.assess(29.79, -95.64))
    assert out["verdict"] == "no_flags" and out["info"][0]["code"] == "reservoir_area"
    assert asyncio.run(parking.assess(29.79, -95.64, simulate=True))["verdict"] == "move"
    monkeypatch.setattr(reservoir, "get_pool", pool_hi)
    out = asyncio.run(parking.assess(29.79, -95.64))
    assert out["verdict"] == "move" and out["reasons"][0]["code"] == "reservoir_pool"
