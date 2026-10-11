# Cycle 26 plan (freeze 11:00 AM CDT Sun Oct 11; each builder budget <= 2 h)

Source research: docs/cycles/cycle-26-research.md. Rule reminders: stay in your folder, no API keys needed, every fact carries a source URL, "Call 911" copy untouched.

## A. Accuracy fixes (do first, ~45 min total, all four builders in parallel)

### A1. NFIP 30-day wait has exceptions (highest priority)
Source: https://www.floodsmart.gov/get-insured/buy-a-policy (exceptions: mortgage made/increased/extended/renewed = no wait; coverage change at renewal = no wait; 1-day wait for newly designated high-risk zone; 1-day wait after wildfire-caused flooding).

Where the stale claim lives and the fix:
1. `backend/app/services/insurance.py` (backend agent). Messages say "NO flood coverage" until day 30 with no caveat. Add field `exceptions_note` (str) and `exceptions_note_code: "ins.exceptions"` to the return dict. Text: "Exceptions exist: there is generally no wait when the policy is required for a mortgage that is made, increased, extended or renewed, or when you change coverage at renewal. Ask your agent." Change both message strings: "...Until then you generally have NO flood coverage (a few exceptions exist, such as buying with a mortgage)." Keep `days_wait:30` and `source`. Add to `message_params` nothing new.
2. `frontend/src/i18n/p12.ts` (frontend agent) lines ~107-108 (`ins.covered`, `ins.late`, en) and the es/vi/zh/ar copies at ~217, 327, 437, 547: add "generally" to the no-coverage sentence and add new key `ins.exceptions` in all 5 languages with the sentence above. `frontend/src/api.ts` line 66 `Countdown` type: add `exceptions_note?: string; exceptions_note_code?: string`. Render it as a small muted line under the countdown message on the Prepare page (`prep.ins` section in `frontend/src/i18n.ts` line 70 is the title; find the component that calls `api.countdown`), with a SourceLink to the FloodSmart URL.
3. `frontend/src/i18n.ts` line 59 `home.c4`: "Remember flood insurance has a 30-day wait. Buy before the storm is in the forecast." change to "Most new flood insurance policies have a 30-day wait (a few exceptions, like buying with a mortgage). Buy before a storm is in the forecast." (other languages: via i18n-fill if keys exist there; otherwise fall back to English is acceptable).
4. `backend/app/ai/graph.py` line ~495 (AI agent): "Flood insurance takes 30 days to start; buy today and you are covered from {date}" becomes "Flood insurance generally takes 30 days to start (exceptions exist, e.g. buying with a mortgage; ask your agent); buy today and coverage generally starts {date}".
5. `data/knowledge/insurance-30-day-and-gap.md` (data agent): replace the first bullet with: `"Your flood insurance coverage will go into effect 30 days after your date of purchase." Exceptions: no wait when a mortgage is made, increased, extended or renewed, or when coverage is changed at renewal; a 1-day wait applies to property newly designated high-risk (bought within 12 months of the map update) and after wildfire-caused flooding. (FloodSmart.gov)` Keep source line. Also confirm 92% only appears as the quoted line (already true; frontend grep for "92%" returned nothing to fix).
6. `frontend/src/components/season/ics.ts` line 34 comment only; reminder at 45 days is fine, no change.

### A2. Flood-bond figures are stale
Source: https://communityimpact.com/cypress/government/a-new-vision-harris-county-restructures-2018-bond-projects-and-funding/ (fall 2025 restructure: 54 packages completed, 75 of remaining 116 moving forward, 26 paused, 15 closed as not feasible; quarterly dashboard).
Locations (all hold the auditor's March 2025 numbers, which are correctly dated but read as current):
- `data/civic.json` bond.facts (data agent): keep the two March 2025 facts, rewording the first to "Harris County auditor memo, June 2025: by March 2025, 43 of 181 projects in the 2018 flood bond program were complete." and add a new first fact: text "The county restructured the 2018 bond program in fall 2025: 54 project packages completed, 75 of the remaining 116 moving forward, 26 paused and 15 closed as not feasible. Check the HCFCD dashboard for current status." source = the Community Impact URL above.
- `data/knowledge/flood-bond-and-accountability.md` line 7 (data agent): same rewording plus the restructuring bullet with the Community Impact source line.
- `frontend/src/i18n/p12.ts` keys `civic.bond.0`, `civic.bond.1` (~lines 80-81 and the 4 other languages) (frontend agent): mirror the civic.json order. Keys are index-based, so adding a fact at index 0 shifts translations; instead APPEND the new fact at the END of the facts list (becomes `civic.bond.5`; add to all 5 languages) to keep existing indices valid. Data agent must therefore append, not prepend, in civic.json.
- `data/demo_snapshot/GET__api_civic-*.json` (4 files; data agent): regenerate with `scripts/refresh_snapshots.py` after the civic.json change (or hand-patch bond.facts identically).
- `docs/sources.md` is research agent territory; leave alone.

### A3. MAAPnext timeline
Source: https://communityimpact.com/cypress/government/harris-county-officials-publish-draft-fema-flood-map-data-talk-next-steps/ ("may not be final until 2028").
- `data/knowledge/outdated-maps-and-maptool-status.md` line 9 (data agent): replace "They are expected to take effect in about 2-3 years." with "County officials say the new maps may not be final until 2028 (Community Impact, Oct 2025 reporting)." Add the Community Impact URL as a source line at top.
- No other occurrence in code (grep of backend/app, frontend/src found none).

### A4. Bugs found by reading code
- B1 (minor, backend `backend/app/services/gauges.py` 63-65): when an observation is stale the stage is set to None and status becomes "unknown", losing the last reading entirely. Keep `last_stage_ft` so the UI can say "last reported X ft, N hours ago". Optional, only if time remains.
- B2 (backend `backend/app/services/outlook.py`): hard-coded `LAYER = 0` and no `valid_time`; the Day 1 label never says when the outlook is valid. Fixed naturally by item C3 below.
- B3 (backend `insurance.py`): `_season_end` returns the same-year Nov 30 even when the purchase date is Dec 1 to Jan 31 (off season); that is correct. No bug, but the "late" message says "Buy earlier next year" even in December when the next season is 6 months away; acceptable.
- B4 (alerts, backend `backend/app/services/alerts.py` line 14): drops NWS `parameters` (flash flood damage threat tag). Research item 6 is unverified; do NOT build this cycle.

## B. Ranked backlog (impact x demo value / effort)
| Rank | Item | Impact | Demo | Effort | Decision |
|---|---|---|---|---|---|
| 0 | A1-A3 accuracy fixes | very high | n/a | 45 min | DO FIRST |
| 1 | C1 Gauge impact statements and Harvey crest | high | high | 1.5 h | BUILD |
| 2 | C2 FEMA NRI neighborhood chip | medium | high (equity story) | 1 h | BUILD |
| 3 | C3 WPC outlook Days 2-5 strip | medium | medium (needs simulate) | 1 h | BUILD |
| 4 | "How rare is this rain" (MRMS + Atlas 14) | high | high | 2 h | CUT (too tight, two external services, units unverified) |
| 5 | FEMA aid by ZIP (Harvey) | medium | medium | 1.5 h | CUT / stretch if data agent idles |
| 6 | NWS warning-tier highlight | medium | low | 1 h | CUT (field unverified) |

## C. Features to build

### C1. Gauge impact statements and historic crests
Source: `GET https://api.water.noaa.gov/nwps/v1/gauges/{LID}` (`flood.impacts[{stage,statement}]`, `flood.crests.historic[{occurredTime,stage}]`). Attribution URL: https://water.noaa.gov/gauges/{LID} (NWS/NOAA NWPS).

Ownership:
- Data agent (`scripts/fetch_gauge_impacts.py` -> `data/gauge_impacts.json`): for each gauge in `data/gauges.json` (36 gauges; use `id` as LID), fetch the endpoint once, write `{ "<LID>": {"impacts":[{"stage":38.5,"statement":"..."}], "harvey_crest":{"stage":109.09,"occurred":"2017-08-30"}|null, "source":"https://water.noaa.gov/gauges/<LID>"} }`. Harvey crest = the historic crest with occurredTime on 2017-08-25 to 2017-09-05, else null. Empty impacts list is valid (HSIT2, HFFT2, MBVT2). Must tolerate per-gauge failure.
- Backend agent: in `backend/app/services/gauges.py` `gauge_status()` add `impact:{current:{stage,statement}|null, next:{stage,statement}|null, harvey_crest_ft:float|null, harvey_delta_ft:float|null, source}|null`. `current` = highest impact with stage <= stage_ft; `next` = lowest impact with stage > stage_ft; `harvey_delta_ft` = harvey crest minus current stage (null when stage unknown). Load the JSON once (module-level, like `load_gauges`); return `impact:null` if the file or gauge is missing. Additive field only, existing keys unchanged. Under `simulate=True` the simulated stage drives the same logic.
- Frontend agent: in `frontend/src/api.ts` add the `impact` type to `Gauge`; on the gauge cards in `frontend/src/components/home/LiveConditions.tsx` (gauge row near lines 40-45) add a collapsible "What this level means" line: current statement, "Next impact at X ft: ...", and "Harvey crest was N ft (D ft above today)" with a SourceLink "NWS NWPS". Hide when `impact` is null or has no impacts. Mobile-first, i18n keys in a new `frontend/src/i18n/p26.ts` (en/es/vi/zh/ar; statement text stays English, label that it is NWS text).
- AI agent: no change required (gauge data flows through `get_risk`); optionally append the nearest gauge's `impact.current.statement` to the risk summary in `backend/app/ai/graph.py`.

Acceptance:
1. `uv run python scripts/fetch_gauge_impacts.py` writes entries for all 36 gauges; HGTT2 has 5 impacts including the "above 38.5 feet" statement; BAKT2 has 10 incl. 101.56 ft pool of record; ADDT2 harvey_crest.stage == 109.09.
2. `curl "localhost:8000/api/risk?lat=29.7&lon=-95.4"` nearest_gauges[*].impact present; offline gauge gives `impact.current:null`, no crash.
3. `?simulate=storm` on `/watch/status` shows a non-null `impact.current` for at least one gauge with impacts.
4. Gauges with zero impacts render no empty card section. pytest passes; no API key needed.

### C2. FEMA National Risk Index neighborhood chip
Source: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Census_Tracts/FeatureServer/0/query ; public page https://hazards.fema.gov/nri/ (FEMA National Risk Index).

Ownership:
- Backend agent (single owner): new `backend/app/services/nri.py` + `backend/app/routers/nri.py`, register in `backend/app/main.py` router tuple. `GET /api/nri?lat&lon` -> `{tract, inland_flood:{rating, annual_freq_events}, expected_loss_rating, resilience:{rating}, social_vulnerability:{rating}, overall_risk:{rating}, population, source, note, meta}` or `{available:false, warnings:[...]}` on failure. Use outFields exactly `TRACTFIPS,IFLD_RISKR,IFLD_EALR,IFLD_AFREQ,RESL_RATNG,SOVI_RATNG,RISK_RATNG,POPULATION` (do NOT request `RFLD`; invalid field = 400). Params: geometry=`lon,lat`, geometryType esriGeometryPoint, inSR 4326, spatialRel esriSpatialRelIntersects, returnGeometry false, f json. Use `app.services.http.get_json` with ttl 86400 and `meta` like other endpoints. Note text: "Statistical index for the census tract, not your house." Also add the same dict under key `nri` in `/risk` ONLY if cheap (wrap in try; never slow `/risk`). Prefer standalone endpoint.
- Frontend agent: chip "Neighborhood context" on `frontend/src/components/home/PlaceProfile.tsx` (it already hosts the MAAPnext SourceLink): "Inland flood risk: Very High. Community resilience: Very Low. Social vulnerability: Very Low (FEMA NRI, tract level)". Add `api.nri()` in `frontend/src/api.ts`, i18n keys in `frontend/src/i18n/p26.ts`. Hide on `available:false`. Do not color-code resilience/vulnerability as personal judgment; plain neutral chip.
- Data agent: add `data/knowledge/neighborhood-risk-index.md` (short card: what NRI is, rating scale, caveats, source URL above) so Ask can explain it. AI agent: add `get_nri` tool only if the router tuple stays simple; otherwise RAG card is enough (skip tool).

Acceptance:
1. `curl "localhost:8000/api/nri?lat=29.6870&lon=-95.4698"` returns tract 48201420800, inland_flood.rating "Very High", population 2274.
2. A point outside the US/ocean returns `available:false` with 200.
3. Chip renders on Home after a Meyerland address lookup; hidden when endpoint fails (simulate by offline).

### C3. WPC Excessive Rainfall outlook Days 2-5
Source: https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer (layers 0..4 = Day 1..5; fields outlook, valid_time, issue_time).

Ownership:
- Backend agent: extend `backend/app/services/outlook.py`; keep `day1` unchanged, add `days:[{day:1..5, category, label, valid_time|null}]` and `max_category` (highest of days 1-5), and `prepare_nudge: bool` (true if any day >= "Slight"). Query layers 0-4 in parallel (`asyncio.gather`), tolerate per-layer failure (mark that day `category:null`, add warnings). `?simulate=storm` on `/outlook` makes days 2-3 "Moderate" and day 1 "Slight" so the demo works without a stormy day (add `simulate: bool = False` param in `backend/app/routers/outlook.py`).
- Frontend agent: 5-chip strip "Day 1 ... Day 5" in the existing outlook UI (find usage of `api.outlook`); when `prepare_nudge` show the existing "Prepare" nudge. i18n keys in `p26.ts`.
- AI agent: none.

Acceptance:
1. `/api/outlook?lat=29.76&lon=-95.37` returns 5 `days`, `day1` still present (no frontend regression).
2. `/api/outlook?lat=29.76&lon=-95.37&simulate=storm` has `prepare_nudge:true`.
3. Single layer failure still returns 200 with a warning.

## D. Builder assignments (one per folder, 4 builders)
1. Data agent (`data/` + `scripts/`): A1.5, A2 (civic.json append, knowledge md, regenerate demo_snapshot civic files), A3, C1 script + `data/gauge_impacts.json`, C2 knowledge card. Order: A-items first (20 min), then C1 script (45 min).
2. Backend agent (`backend/` excl. `app/ai`): A1.1, C1 service (after data file exists; develop against a 2-gauge stub), C2 endpoint, C3 outlook. Order: A1, C3, C2, C1.
3. AI agent (`backend/app/ai/`): A1.4 graph.py wording; add 3 questions to `data/eval/questions.jsonl` is data territory, so instead tell the data agent: add "Is there a waiting period if I buy flood insurance with a mortgage?" and "When will the new Harris County flood maps be final?" to `data/eval/questions.jsonl`; AI agent then runs `scripts/eval_ai.py` for a regression check and confirms RAG picks up the changed knowledge cards (re-index). Light load; also owns optional nearest-gauge impact sentence in graph.py (C1).
4. Frontend agent (`frontend/`): A1.2-A1.3, A2 i18n, C1 UI, C2 chip, C3 strip, new `frontend/src/i18n/p26.ts`; run `scripts/i18n_coverage.mjs` before reporting.

Merge order: data A-items and backend A1 land first; frontend consumes new fields defensively (optional types), so no hard dependency between builders. Everyone: report briefly what works, run command, stubs, blockers by 10:30 AM.
