from app import freshness
from app.services.alerts import is_storm_trigger
from app.services.gauges import gauge_status


def test_advisory_is_not_storm_trigger():
    assert not is_storm_trigger({"event": "Coastal Flood Advisory"})
    assert is_storm_trigger({"event": "Flash Flood Warning"})


def test_simulated_gauge_never_marks_storm():
    import asyncio
    freshness.clear_storm()
    g = {"id": "X", "nwps_id": "ZZZZ9", "lat": 29.7, "lon": -95.3, "name": "t",
         "flood_stages": {"action": 10, "minor": 12, "moderate": 14, "major": 16}}
    asyncio.run(gauge_status(g, simulate=True))
    assert not freshness.storm_on()


def test_storm_expires():
    freshness.mark_storm()
    assert freshness.storm_on()
    freshness._storm_until = 0.0
    assert not freshness.storm_on()
