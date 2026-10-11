"""Per-sentence citations and as-of freshness (no network)."""
from app.ai import citations, graph, routing


def test_attach_maps_sentences_and_drops_invalid():
    r = citations.attach({"answer": "Insurance waits 30 days [1]. Claims peaked in 2017 [3]. It may rain.\nNot official guidance.",
                          "sources": ["https://a.example", "https://b.example"]})
    assert r["citations"] == [{"sentence_index": 0, "source_index": 0}]
    assert "[3]" not in r["answer"]
    assert r["uncited"] == [1]  # numeric claim, its only marker pointed at a source that was never retrieved


def test_lone_marker_joins_previous_sentence():
    r = citations.attach({"answer": "ZIP 77096 has 40 claims. [1]", "sources": ["https://a.example"]})
    assert r["citations"] == [{"sentence_index": 0, "source_index": 0}] and r["uncited"] == []


def test_asof_phrase_local_time_and_provisional():
    res = {"meta": {"as_of": "2026-10-11T20:42:00Z", "provisional": True}}
    assert citations.asof_phrase(res) == " (as of 3:42 PM CDT, provisional)"
    assert citations.asof_phrase({}) == "" and citations.asof_phrase({"meta": {"as_of": "junk"}}) == ""


def test_template_states_gauge_and_alert_as_of():
    meta = {"as_of": "2026-10-11T20:42:00Z", "provisional": True}
    s = {"lang": "en", "question": "is it flooding", "intents": ["risk"], "context": [],
         "tool_results": {"get_risk": {"fema_zone": "AE", "sfha": True, "nearest_gauges": [{"name": "Brays", "status": "normal"}], "meta": meta},
                          "get_alerts": {"alerts": [], "meta": meta}}}
    a = graph._answer(s)["answer"]
    assert a.count("as of 3:42 PM CDT, provisional") == 2


def test_compact_exposes_local_as_of():
    out = routing.compact("get_alerts", {"alerts": [], "meta": {"as_of": "2026-10-11T20:42:00Z"}})
    assert out["as_of"] == "as of 3:42 PM CDT"


def test_tag_live_adds_tool_source_to_stamped_sentence():
    a, s = citations.tag_live("Gauge is normal (as of 3:42 PM CDT).\nNot official guidance.", ["https://x.example"],
                              "https://nws", "https://noaa", True, False)
    assert a.startswith("Gauge is normal (as of 3:42 PM CDT) [2].") and s == ["https://x.example", "https://noaa"]
