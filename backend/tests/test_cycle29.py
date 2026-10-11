import asyncio
import json
from datetime import datetime, timedelta, timezone

from app.services import civic, floodhistory, officials, route


def test_report_rule():
    assert not route.report_counts("street_flooding", 5)
    assert not route.report_counts("flooded_road", 0)
    assert route.report_counts("flooded_road", None)
    assert route.report_counts("water_over_road", 8)


def test_recent_reports_filters(monkeypatch):
    from app.db import Report, get_session
    now = datetime.now(timezone.utc)
    rows = [Report(lat=1, lon=1, kind="flooded_road", depth_in=0, created_at=now),
            Report(lat=2, lon=2, kind="water_over_road", depth_in=8, created_at=now - timedelta(hours=1)),
            Report(lat=3, lon=3, kind="flooded_road", depth_in=8, created_at=now - timedelta(hours=7)),
            Report(lat=4, lon=4, kind="street_flooding", depth_in=9, created_at=now)]
    with get_session() as s:
        ids = []
        for r in rows:
            s.add(r)
        s.commit()
        ids = [r.id for r in rows]
    try:
        got = {r["lat"] for r in route.recent_reports()}
        assert 2 in got and not ({1, 3, 4} & got)
    finally:
        with get_session() as s:
            for i in ids:
                s.query(Report).filter(Report.id == i).delete()
            s.commit()


def test_short_name_and_more(monkeypatch):
    feats = [{"geometry": {"coordinates": [-95.0 - i * 1e-5, 29.0]},
              "properties": {"id": f"x{i}", "name": "LONG " * 30, "short_name": f"Short {i}", "risk": "high", "reasons": ["r"]}}
             for i in range(5)]
    monkeypatch.setattr(route, "load_crossings", lambda: feats)
    monkeypatch.setattr(route, "recent_reports", lambda: [])

    async def osrm(*a, **k):
        return {"routes": [{"geometry": {"type": "LineString", "coordinates": [[-95.1, 29.0], [-94.9, 29.0]]}}]}

    async def al(*a, **k):
        return {"alerts": []}

    async def ng(*a, **k):
        return []
    monkeypatch.setattr(route, "get_json", osrm)
    monkeypatch.setattr(route.diskcache, "get", lambda *a: None)
    monkeypatch.setattr(route.diskcache, "put", lambda *a: None)
    monkeypatch.setattr(route, "get_alerts", al)
    monkeypatch.setattr(route, "nearest_gauges", ng)
    r = asyncio.run(route.check_route({"lat": 29.0, "lon": -95.1}, {"lat": 29.0, "lon": -94.9}))
    assert "Short 0" in r["message"] and "+2 more" in r["message"] and "LONG" not in r["message"]


def test_crossing_names_short():
    from app.services.data import load_json
    for f in (load_json("crossings.geojson", {}) or {}).get("features", []):
        p = f["properties"]
        n = p.get("short_name") or p.get("name") or ""
        if p.get("short_name"):
            assert len(n) <= 80


def test_officials_parallel_and_empty_member(monkeypatch):
    officials._cache.clear()

    async def at(url, lat, lon, fields):
        if url == officials.PRECINCT_URL:
            return {"PCT_NO": 1, "COMMISSION": "X", "URL": "u"}
        if url == officials.ADMIN_URL:
            return {"Entity": "City of Houston", "Administrator": "A"}
        return {"DISTRICT": "C", "MEMBER": "", "PHONE": None}
    monkeypatch.setattr(officials, "_at", at)
    o = asyncio.run(officials.get_officials(29.7, -95.4))
    assert o["council"]["member"] is None and o["council"]["district"] == "C"

    officials._cache.clear()

    async def at2(url, *a):
        if url == officials.ADMIN_URL:
            return {"Entity": "Harris County"}
        return {"DISTRICT": "C", "MEMBER": "Z"}
    monkeypatch.setattr(officials, "_at", at2)
    assert asyncio.run(officials.get_officials(29.9, -95.9))["council"] is None


def test_civic_cached_and_deduped(monkeypatch):
    civic._cache.clear()
    calls = {"n": 0}

    async def build(lat, lon):
        calls["n"] += 1
        await asyncio.sleep(0.05)
        return {"officials": {"commissioner": {"x": 1}}}
    monkeypatch.setattr(civic, "_build_civic", build)

    async def go():
        await asyncio.gather(civic.get_civic(29.7001, -95.4), civic.get_civic(29.7002, -95.4))
        await civic.get_civic(29.7, -95.4)
    asyncio.run(go())
    assert calls["n"] == 1


def test_flood_history_zip_timeout_partial(monkeypatch):
    floodhistory._cache.clear()

    async def slow(z):
        raise asyncio.TimeoutError()
    monkeypatch.setattr(floodhistory, "zip_insurance", slow)
    out = asyncio.run(floodhistory.flood_history(29.7, -95.4, "77096"))
    assert out["zip"] is None and out.get("warnings")
