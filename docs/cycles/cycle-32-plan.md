# Cycle 32 plan (freeze 11:00; builders done by ~9:30)

Picked by impact x demo value: A trace stepper, B observed rain, C warning polygons, D report votes. One builder per folder:
backend/app/ai = A, backend/ (excl. ai) = B+C+D endpoints, frontend = all UI, data/scripts = none (optionally DEMO_SNAPSHOT fixture for C). Dep order: backend ships first (~8:15), frontend consumes.

## Verified today (live)
- Open-Meteo `https://api.open-meteo.com/v1/forecast?latitude=29.76&longitude=-95.37&hourly=precipitation&past_days=3&forecast_days=1&precipitation_unit=inch&timezone=UTC` returns 96 hourly values (first 72 = past 72 h, UTC). Today total = 0.0 in (dry), so the demo needs a fixture/simulate path. Model-estimated, not gauge.
- NWS `api.weather.gov/alerts/active?area=TX`: Flood Warning had geometry (1/1); Coastal Flood Advisory had NO geometry (3/3). Zone-only alerts are real and common.

## A. "How I answered" trace stepper (ai owner; frontend renders)
Today: `/ask` (backend/app/ai/router.py:52 -> fast.ask_once) returns only `answer, sources, generated_by, tools_used[names]` (fast.py:489, 561); NO timings, no retrieved chunks. `/ask/stream` final (fast.py:379-382) has `tools_used` + `timings{first_speak_ms,total_ms}` + `citations`; no per-step data. Frontend never reads tools_used/timings (grep: 0 hits in frontend/src). Ask uses `api.ask` (Ask.tsx:236), not stream, for text.
Add (no new Gemini calls) to both `/ask` and stream `final`: `trace:{intent:str, route:"prefetch"|"graph"|"cache"|"template", retrieved:[{title,source,score?}] (max 3, from s["context"]), tools:[{name, ms}], answer:{by:"gemini"|"template", ms}, total_ms}`. Time tool calls where `_guard(run_tool...)` runs (fast.py ~415, 469, 486, 543). Keep always present; empty lists when absent.
UI: collapsible "How I answered" under each assistant bubble in components/ask/MessageList.tsx: 4 steps (Understand > Search sources > Check live data > Write answer) with chunk titles linking to source URLs, tool names + ms, "template (no API key)" badge. Not official guidance copy stays.
Accept: with no GEMINI key `POST /api/ask {"question":"Is 77096 at flood risk?","lang":"en","lat":29.69,"lon":-95.49}` has `trace.tools.length>=1`, `trace.retrieved[0].source` starts with http; UI shows stepper; pytest for shape; cached hit still returns trace (route:"cache").

## B. Rain already fallen (backend; frontend card)
`GET /rain24` gains `past:{available:bool, last24_in, last72_in, peak_hour:{t,in}|null, source:"Open-Meteo (model-estimated, not a rain gauge)", source_url:"https://open-meteo.com/en/docs", gauge_url:"https://www.harriscountyfws.org"}` fetched in services/rain24.py via services/http.get_json, TTL 900 (freshness.effective_ttl), failure -> `past.available:false`, never break existing fields. Sum values ending at "now" (hour <= current UTC hour), round 2. Also add `past` to the ai tool result for rain24 (ai owner one-line pass-through: tools.py) so Ask can answer "has it rained a lot?" (coordinate: backend owner only exposes it; ai owner edits tools.py).
UI: line in components/rain24/RainCard.tsx (+ Home): "0.8 in fell in the last 24 h (3-day: 1.9 in) - model estimate, not a gauge. Check gauges: Harris County FWS". Hide when unavailable; i18n 5 languages.
Accept: `curl '/api/rain24?lat=29.76&lon=-95.37'` -> `past.last72_in` numeric; unit test with fixture hourly array (sum correct); offline -> available:false, card still renders.

## C. Active flood-warning polygons (backend; frontend map layer)
New `GET /alerts/area?bbox=minx,miny,maxx,maxy` (routers/alerts.py + services/alerts.py): fetch `https://api.weather.gov/alerts/active?area=TX` once (User-Agent per CLAUDE.md, cache 90 s storm/300 s else), keep events matching Flood Warning|Flash Flood Warning|Flood Watch|Flash Flood Watch|Flood Advisory|Coastal Flood *. Return GeoJSON FeatureCollection: `properties:{id, event, severity, headline, expires, has_geometry:bool, area_desc, source:"https://api.weather.gov/alerts/<id>"}`; geometry = alert geometry if present and intersects bbox, else null. Zone-only alerts (no geometry) go in top-level `zone_only:[{event, headline, area_desc, expires}]` (skip fetching zone shapes: out of time budget). `meta` via freshness.with_meta. Bad upstream -> empty collection + meta.freshness:"cached", never 500. Also DEMO_SNAPSHOT fixture with one synthetic-free copy of a real captured warning (data owner optional).
UI: toggle "Active NWS warnings" in components/maps.tsx (react-leaflet GeoJSON; red Flash Flood Warning, orange Flood Warning, amber Watch/Advisory), popup headline + expires + source link; zone-only alerts as chips above map; Freshness component. Default ON in Home map when any returned.
Accept: `/api/alerts/area?bbox=-96.5,29,-94.5,30.5` returns valid JSON in <1.5 s warm; features with null geometry never reach Leaflet (frontend filters); empty state shows "No active flood warnings in view (NWS)".

## D. Still there / cleared votes (backend; frontend)
db.py:15 Report has composite PK (id, created_at) and no vote fields. Add columns `confirms INT default 0, clears INT default 0, last_vote_at DateTime null` (migration: guarded `ALTER TABLE ... ADD COLUMN` in db init, wrapped try, sqlite+pg; plain-table fallback). `POST /reports/{id}/vote {still_there:bool}` -> `{id, confirms, clears, last_vote_at}`; 404 unknown id; per-IP rate limit via ratelimit.py, plus client dedupe in localStorage. `_row` (routers/reports.py:19) and `recent_reports()` (services/route.py:22) include the counts; rule: `clears>=2 and clears>confirms` -> excluded from route hazards (route.py ~report_counts) and shown as "Cleared". Hazard `reason` text: "3 people confirmed, last 12 min ago (community report, unverified)".
UI: buttons "Still there" / "Cleared" on report popups and in Drive hazard list; counts + relative time; thanks toast; always "unverified, Call 911 for rescue".
Accept: post report, vote clear x2 -> `/api/route-check` hazard gone; vote confirm -> counts rise; 429 on spam; existing reports with null counts treated as 0.

## Bugs / risks spotted
1. `/ask` error fallback (ai/router.py:59-63) omits `warnings`/`speak`-parity and any `trace`; fine but frontend must default missing `trace`.
2. Reports list is NOT filtered by age (routers/reports.py:37-47) while route uses 6 h (route.py:11); stale reports render on maps indefinitely. Add `since_hours` default 24 to GET /reports (backend, 5 min).
3. `POST /reports` accepts no rate limit/dedupe visible in the router (ratelimit.py exists but not imported here) -> spam can flip route verdicts.
4. Ask text path uses non-stream `/ask` so `timings` never reach the UI; the stream `final` (fast.py:379) is the only place with timings.
5. Cycle-32 research suggests `forecast_days=0`; Open-Meteo returns only past data then, fine, but use `forecast_days=1` so the current hour exists.
6. Dry day: B shows 0.0 in and C may show nothing; demo needs ?simulate/DEMO_SNAPSHOT fixtures.
