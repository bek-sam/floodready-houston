"""Flood history / ZIP insurance / medical tools in the no-key template path."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for k in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "BACKBOARD_API_KEY"):
    os.environ[k] = ""

from app.ai import graph, tools  # noqa: E402

HARVEY = "https://example.org/harvey"
ZIPSRC = "https://example.org/openfema"
MEDSRC = "https://example.org/cms"


def _stub(monkeypatch):
    async def fh(lat, lon, z=None):
        return {"harvey": {"flooded": True, "source": HARVEY},
                "events": [{"id": "harvey-2017", "name": "Harvey", "start": "2017-08-25",
                            "nearest_gauge": {"id": "g", "name": "Buffalo Bayou", "distance_mi": 1.2, "peak_ft": 40.1, "peak_category": "major"}}],
                "zip": None}

    async def zi(z):
        return {"zip": z, "claims": {"total": 120, "since_2017": 90, "by_year": []}, "policies_in_force": 300, "source": ZIPSRC}

    async def nb(lat, lon, kind="dialysis", limit=5):
        return {"facilities": [{"name": "Test Dialysis", "phone": "555-0100", "distance_mi": 0.8}], "source": MEDSRC, "note": "Call first."}

    import app.services.floodhistory as a, app.services.zipinsurance as b, app.services.medical as c
    monkeypatch.setattr(a, "flood_history", fh)
    monkeypatch.setattr(b, "zip_insurance", zi)
    monkeypatch.setattr(c, "nearby", nb)


def _ask(q, lang="en", lat=29.69, lon=-95.46):
    return asyncio.run(graph.ask(q, lang, lat, lon))


def test_intents():
    c = lambda q: graph.classify_intent({"question": q})["intents"]
    assert "flood_history" in c("Did my neighborhood flood before?")
    assert "street_flood" not in c("Has my house flooded before?")
    assert "flood_history" in c("¿Se inundó mi zona antes?")
    assert "zip_insurance" in c("Is flood insurance common here?")
    assert "zip_insurance" in c("how many claims in my zip 77025")
    assert "medical_site" in c("dialysis center near me")
    assert "medical_site" in c("centro de diálisis cerca")


def test_history_answer_leads_with_tool(monkeypatch):
    _stub(monkeypatch)
    j = _ask("Did my neighborhood flood before?")
    assert "get_flood_history" in j["tools_used"] and HARVEY in j["sources"]
    assert j["answer"].startswith("This location was inside") and "Buffalo Bayou" in j["answer"]


def test_zip_and_medical(monkeypatch):
    _stub(monkeypatch)
    j = _ask("Are flood insurance claims common in my zip 77025?")
    assert "get_zip_insurance" in j["tools_used"] and ZIPSRC in j["sources"] and "120" in j["answer"]
    j = _ask("dialysis center near me")
    assert "get_medical" in j["tools_used"] and MEDSRC in j["sources"] and "Test Dialysis" in j["answer"]
    j = _ask("¿Es común el seguro de inundación aquí? código 77025", "es")
    assert "reclamos" in j["answer"]


def test_zip_missing_prompt(monkeypatch):
    _stub(monkeypatch)
    assert "ZIP" in _ask("is flood insurance common here")["answer"]


def test_tool_missing_returns_error(monkeypatch):
    import importlib
    real = importlib.import_module
    monkeypatch.setattr(importlib, "import_module", lambda n, *a: (_ for _ in ()).throw(ImportError()) if n.endswith("medical") else real(n, *a))
    assert asyncio.run(tools.run_tool("get_medical", {"lat": 1, "lon": 2})) == {"error": "unavailable"}
