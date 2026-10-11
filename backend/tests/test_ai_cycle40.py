"""Cycle 40: new agent tools (reservoir, declarations, rain, NRI, emPOWER, parking) and their intent routing."""
import asyncio
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for k in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "BACKBOARD_API_KEY"):
    os.environ[k] = ""

from app.ai import graph, live, routing, tools  # noqa: E402

SRC = {"reservoir": "https://water.noaa.gov/gauges/ADDT2", "declarations": "https://www.fema.gov/about/openfema/data-sets",
       "nri": "https://hazards.fema.gov/nri/", "empower": "https://catalog.data.gov/dataset/hhs_empower_rest_service_public"}

FAKE = {
    ("reservoir", "get_pool"): {"available": True, "relevant": True, "ground_elevation_ft": 90.0, "pool_below_ground_ft": 5.0,
                                "pool": {"stage_ft": 85.0, "status": "normal", "action_ft": 92, "minor_ft": 95, "gauge_id": "x", "name": "n"},
                                "datum_note": "long " * 50, "meta": {"a": 1}, "source": SRC["reservoir"]},
    ("declarations", "status"): {"available": True, "active_ia": False, "source": SRC["declarations"], "note": "n",
                                 "latest": {"title": "SEVERE STORMS", "declaration_date": "2026-06-01", "disaster_number": 1, "url": "u"},
                                 "recent": [{"title": "SEVERE STORMS"}, {"title": "HURRICANE BERYL", "declaration_date": "2024-07-08"}]},
    ("rain24", "get_rain24"): {"available": True, "total_inches": 0.4, "windows": [{"x": 1}] * 20, "pop_hourly": [{"x": 1}] * 24,
                               "max_pop_pct": 40, "action": {"show": False, "text": None}, "source": "NWS label", "source_url": "https://www.weather.gov",
                               "past": {"available": True, "last24_in": 1.25, "last72_in": 2.0, "peak_hour": None}},
    ("nri", "get_nri"): {"available": True, "inland_flood": {"rating": "Relatively High"}, "overall_risk": {"rating": "x"},
                         "tract": "48201", "source": SRC["nri"]},
    ("empower", "get_empower"): {"zip": "77025", "available": True, "power_dependent_devices": 410, "oxygen": 120, "dialysis": 5,
                                 "source": SRC["empower"], "map": "m", "puc": {"url": "https://x/puc.pdf", "note": "n"}},
    ("parking", "assess"): {"verdict": "move", "headline": "Consider moving your car", "reasons": [{"code": "c", "text": "FEMA zone AE"}],
                            "fema_zone": "AE", "harvey_flooded": True, "elevation_ft": 40, "crossings_within_300m": [],
                            "active_flood_alerts": [], "higher_ground": None, "limits": "long", "sources": ["https://msc.fema.gov/portal/home"]},
}


def _fake_all(monkeypatch):
    for (mod, fn), val in FAKE.items():
        async def f(*a, _v=val, **k):
            return dict(_v)
        monkeypatch.setattr(importlib.import_module(f"app.services.{mod}"), fn, f)


CASES = {
    "get_reservoir_pool": {"lat": 29.78, "lon": -95.6}, "get_declarations": {}, "get_rain": {"lat": 29.7, "lon": -95.4},
    "get_nri": {"lat": 29.7, "lon": -95.4}, "get_power_dependent": {"zip": "77025"}, "get_parking": {"lat": 29.7, "lon": -95.4},
}


def test_tools_compact_and_sourced(monkeypatch):
    _fake_all(monkeypatch)
    for name, args in CASES.items():
        assert name in tools.TOOLS_BY_NAME and name in tools.TOOL_SOURCE and name in tools.TOOL_TTL
        r = asyncio.run(tools.run_tool(name, args))
        assert isinstance(r, dict) and "error" not in r, name
        j = routing.tool_json(name, r)
        assert len(j) <= routing.MAX_TOOL_CHARS and "datum_note" not in j and "windows" not in j and "limits" not in j, name
        assert str(r.get("source", "")).startswith("http"), name
    assert '"last24_in":1.25' in routing.tool_json("get_rain", asyncio.run(tools.run_tool("get_rain", CASES["get_rain"])))
    assert "HURRICANE BERYL" in routing.tool_json("get_declarations", FAKE[("declarations", "status")])


def test_tool_error_is_graceful(monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(importlib.import_module("app.services.nri"), "get_nri", boom)
    assert asyncio.run(tools.run_tool("get_nri", CASES["get_nri"])) == {"error": "unavailable"}


def test_medical_passes_flood_exposure():
    r = {"facilities": [{"name": "D", "phone": "1", "distance_mi": 1, "fema_zone": "AE", "sfha": True, "harvey_flooded": False, "lat": 1}], "source": "https://s"}
    f = routing.compact("get_medical", r)["facilities"][0]
    assert f["fema_zone"] == "AE" and f["sfha"] is True and f["harvey_flooded"] is False and "lat" not in f


ROUTES = [
    ("Is the Addicks reservoir high right now?", "get_reservoir_pool", "reservoir_pool"),
    ("¿Está alto el embalse de Barker?", "get_reservoir_pool", "reservoir_pool"),
    ("Is there a FEMA declaration for Harris County?", "get_declarations", "declarations"),
    ("¿Hay declaración de desastre de FEMA?", "get_declarations", "declarations"),
    ("How much rain fell in the last day?", "get_rain", "rain"),
    ("¿Cuánta lluvia cayó ayer?", "get_rain", "rain"),
    ("My mom uses oxygen, what if there is an outage in 77025?", "get_power_dependent", "power_dependent"),
    ("Tengo un ventilador y puede haber un apagón en 77025", "get_power_dependent", "power_dependent"),
    ("Where should I park my car tonight?", "get_parking", "parking"),
    ("¿Dónde debo estacionar mi carro?", "get_parking", "parking"),
]


def test_intent_routing_picks_tool():
    for q, tool, intent in ROUTES:
        s = {"question": q, "lang": "en", "lat": 29.7, "lon": -95.4}
        s.update(graph.classify_intent(s))
        assert intent in s["intents"], q
        assert tool in [n for n, _ in routing.select_tools(s)], q


def test_power_needs_zip_and_no_location_skips_loc_tools():
    s = {"question": "what if there is an outage for my oxygen machine?", "lat": 29.7, "lon": -95.4}
    s.update(graph.classify_intent(s))
    assert "get_power_dependent" not in [n for n, _ in routing.select_tools(s)]
    s = {"question": "How much rain fell?"}
    s.update(graph.classify_intent(s))
    assert "get_rain" not in [n for n, _ in routing.select_tools(s)]


def test_trace_shows_official_source_and_template_answer(monkeypatch):
    _fake_all(monkeypatch)
    j = asyncio.run(graph.ask("Is the Addicks reservoir high right now?", "en", 29.78, -95.6))
    assert "get_reservoir_pool" in j["tools_used"] and SRC["reservoir"] in j["sources"]
    assert "85.0 ft" in j["answer"]
    for name in CASES:
        assert tools.TOOL_SOURCE[name].startswith("https://")


def test_live_declarations_cover_new_tools():
    names = {d.name for d in live.tool_declarations()}
    assert set(CASES) <= names
    assert set(CASES) <= set(live.TOOL_LABELS)


def test_template_rain_no_unrelated_bullets_and_declaration_format(monkeypatch):
    _fake_all(monkeypatch)
    j = asyncio.run(graph.ask("How much rain fell here in the last day?", "en", 29.6876, -95.4583))
    assert "1.25 in" in j["answer"]
    assert "\n- " not in j["answer"]
    assert graph._title_case("HURRICANE BERYL") == "Hurricane Beryl"
    assert graph._title_case("DR 4781 STORMS") == "DR 4781 Storms"
    assert graph._fmt_date("2024-07-09T00:00:00.000Z") == "Jul 9, 2024"
    lead = graph._lead_new({"get_declarations": {"source": "s", "latest": {"title": "HURRICANE BERYL", "declaration_date": "2024-07-09"}}},
                           lambda u: "", False)
    assert "Hurricane Beryl (Jul 9, 2024)" in lead[0]
