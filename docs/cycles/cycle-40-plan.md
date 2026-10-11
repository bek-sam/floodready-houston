# Cycle 40 plan — give the AI agent the new data tools (backend/app/ai only)
Gap: Ask (LangGraph + fast path) and Voice (Gemini Live) only know the original 10 tools. Since cycle 25 the backend gained services the agent can't call, so Ask answers "is the Addicks reservoir high?", "is there a FEMA declaration?", "rain in the last day?" from stale knowledge cards only.

AI builder (backend/app/ai/ only; call existing services via the same `_call(module, func, ...)` pattern):
- New tools: `get_reservoir_pool(lat, lon)` (services/reservoir), `get_declarations()` (services/declarations, Harris TX), `get_rain(lat, lon)` (services/rain24 incl. `past`), `get_nri(lat, lon)` (services/nri), `get_power_dependent(zip)` (services/empower), `get_parking(lat, lon)` (services/parking). Keep each tool's JSON compact (only fields an answer needs + source URL) — follow existing compaction helpers.
- Register in ALL_TOOLS, TOOL_SOURCE (official dataset URL per tool), Live `tool_declarations` (short descriptions), and deterministic intent routing (routing.py keyword intents: reservoir/Addicks/Barker → pool; FEMA aid/declaration/disaster assistance → declarations; rain fell/rained/how much rain → rain; outage/oxygen/ventilator/power device → power_dependent; where to park/move my car → parking). Prefetch for voice only if cheap.
- `get_medical`: ensure the new fema_zone/sfha/harvey_flooded fields pass through compaction (Live description already claims "flood exposure").
- Tests (keys blanked): each tool returns compact dict via run_tool with mocked services; intent routing picks the right tool for 2 phrasings each (en + es); trace tools[] shows the official source.
- No live Gemini calls by the builder. Lead runs ≤3 live /ask checks afterwards.
