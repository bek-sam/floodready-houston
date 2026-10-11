# Cycle 32 research: gaps vs leading flood/disaster apps (feature freeze 11 AM; each item <= 1 h)

Method: skimmed CLAUDE.md contract, last 6 CHANGELOG entries (cycles 26-31) and grepped backend/data/frontend. Reference-app behaviour is from each product's public pages (URLs below); items marked VERIFY need a 5-minute endpoint/response check before building. Any user-visible fact must carry a source URL (project rule).

Already covered (do NOT rebuild): watch places + web push (FEMA-app multi-location alerts), NWS alerts, gauges + impact statements (HCFWS-style), crossings + route check (Waze/TranStar-lite), community reports, Turn Around Don't Drown copy in route/plan/Ask, NFIP countdown + ZIP claims/premiums, Harvey extent + HWM, evac zones/surge, tide/storms, rain24 + WPC outlook, parking check, buyouts, civic/officials, shelters (historical), SMS (ReadyHarris-style text), buddy check-in, go-bag/.ics, emPOWER, NRI (First Street-like neighborhood score), widget/share, 5 languages.

## Ranked gaps

### 1. "Rain that already fell" (observed rainfall, last 24/72 h)  [impact: high, effort 45 min]
- Reference: Harris County Flood Warning System shows rain-gauge totals (1/3/6/12/24 h) per gauge - https://www.harriscountyfws.org . Residents use "it already rained 6 in" to judge risk.
- FloodReady: only FORECAST rain (`/rain24`, WPC outlook). No observed totals.
- Smallest version: Open-Meteo (already an approved no-key source) `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=precipitation&past_days=3&forecast_days=0&precipitation_unit=inch`; sum last 24/72 h; add `past:{last24_in,last72_in}` to `/rain24` plus a line on Home ("0.8 in fell in the last 24 h. Source: Open-Meteo, model-based, not a gauge"). Label as model estimate; link HCFWS for gauge truth. Add as agent tool field so Ask can answer "has it rained a lot?".
- Source: https://open-meteo.com/en/docs (past_days parameter).

### 2. Active flood-warning polygons on the map  [impact: high, effort 50 min]
- Reference: NWS/FEMA app and ReadyHarris show the warned AREA, not just "your point has an alert" - https://www.weather.gov , https://api.weather.gov/alerts/active?area=TX&event=Flash%20Flood%20Warning (GeoJSON incl. geometry).
- FloodReady: `/alerts` is per-point text; no polygon layer (VERIFY: grep map layers in frontend/src).
- Smallest: GET `/alerts/area?bbox=` proxying api.weather.gov active Flood/Flash Flood Warning/Watch features (cache 90 s in storm mode, User-Agent per CLAUDE.md), render as a red/amber Leaflet GeoJSON layer with a toggle on the map. Needs `meta` freshness field.

### 3. Confirm / "cleared" on community reports (Waze-style)  [impact: med-high, effort 50 min]
- Reference: Waze lets drivers confirm or dismiss "Flooding"/"Road closed" reports - https://support.google.com/waze/answer/6275483 (reports and "Still there?" / "Not there"). Also ATX Floods shows status of low-water crossings - https://www.atxfloods.com .
- FloodReady: reports expire by age (<=6 h rule) but nobody can confirm or clear one.
- Smallest: POST `/reports/{id}/vote {still_there:bool}`, add 2 columns, show "3 confirmed, last 12 min ago"; a report with >=2 "cleared" votes stops affecting route verdict. Rate-limit by IP (ratelimit.py exists).

### 4. Federal disaster-declaration history for the county  [impact: med, effort 30 min]
- Reference: FEMA app "Disaster Resources" and fema.gov declarations list - https://www.fema.gov/disaster/declarations . Data: OpenFEMA DisasterDeclarationsSummaries v2 (no key) https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state eq 'TX' and designatedArea eq 'Harris (County)' and incidentType eq 'Flood'.
- FloodReady: OpenFEMA NFIP already used; declarations not (VERIFY grep "DisasterDeclarations" = 0 hits expected).
- Smallest: `/flood-history` adds `declarations:{count, latest:[{title,date,disasterNumber}]}`; shows "Harris County: N federal flood-related declarations since 2015". Cite OpenFEMA URL. Strengthens "this is not rare" message in Compare/Home.

### 5. "Is my road/route open" via official road status link-outs  [impact: med, effort 20 min, static]
- Reference: Houston TranStar flooded-roads/closures map - https://traffic.houstontranstar.org ; Harris County FWS road cameras. ReadyHarris also links to them.
- FloodReady: link appears in warnings knowledge card + About; NOT on the route-check result.
- Smallest: after any "caution"/"avoid" route verdict show a "Check official live closures (TranStar)" button + "Call 911 for rescue; 311 for non-emergency". No data fetch, no new facts. (Deep link to the nearest HCFWS gauge page if the page URL pattern is VERIFIED.)

### 6. Offline-first emergency card  [impact: med-high, effort 45 min]
- Reference: Red Cross Emergency app and FEMA app keep checklists/alerts readable without signal - https://www.redcross.org/get-help/how-to-prepare-for-emergencies/mobile-apps.html .
- FloodReady: PWA + wallet card exist (Round 3, cycle 20); VERIFY service worker precaches the last plan, go-bag, Call 911 card and last risk summary for the saved place.
- Smallest: if not cached, add runtime cache (stale-while-revalidate) for `/api/risk`, `/api/plan`, `/api/evac` of saved places and an "Offline - last updated hh:mm" badge using existing Freshness component.

### 7. Plain-language "flood depth to danger" visual  [impact: med, effort 25 min, static]
- Reference: NWS Turn Around Don't Drown - https://www.weather.gov/safety/flood-turn-around-dont-drown (6 in can knock down an adult / reach car bottom; 12 in floats many cars; 2 ft carries away most vehicles - confirm exact wording on page before shipping).
- FloodReady: text in driving-in-floods.md and routes; no visual.
- Smallest: 3-row inline-SVG depth ladder on Drive and under HWM "depth was X in here" (hwm already gives nearest_depth_ft): "Harvey water here was N ft: more than a car's float depth".

### 8. Single-number neighborhood score with "why" (First Street Flood Factor style)  [impact: med, effort 40 min]
- Reference: Flood Factor 1-10 with plain reasons - https://riskfactor.com (First Street). It is proprietary; we must not copy numbers.
- FloodReady: NRI chip + separate facts; no combined view.
- Smallest: NOT a made-up score. Show a "Signals that apply here: n of 6" checklist (SFHA, Harvey flooded, HWM within 2 mi, elevation low_ground, NRI high, crossing <300 m) built only from fields already returned by `/risk`, `/hwm`, `/nri`. Each row has its existing source. Explicitly "not a prediction".

### 9. Texas 211 / Harris County resource handoff by need  [impact: med, effort 20 min, static]
- Reference: ReadyHarris (https://www.readyharris.org) and Red Cross app route people to shelter, supplies, 211.
- FloodReady: 211 appears in medical and civic text; VERIFY it is on the post-flood Recover page first screen.
- Smallest: pin a "Need help now? 911 life-threatening / 211 shelter, food / 311 non-emergency" strip to Recover; copy only.

Not worth doing before freeze: live sandbag/shelter locations (event-specific, no stable keyless feed; shelters stay labelled historical), AlertHouston signup deep integration (county/city enrolment is theirs; keep link), user accounts, crowdsourced photos (moderation).

## Demo-wow quick wins for the agentic AI (no extra Gemini cost)

A. Visible agent trace (30 min). The `final` SSE event already carries `tools_used` and `timings`. Render under each Ask answer a small stepper: classify_intent -> retrieve (3 chunk titles + source links) -> tools (get_risk 120 ms, get_flood_history ...) -> answer (template|gemini). Judges SEE LangGraph + RAG working. Pure frontend; works in template mode.

B. "Ask with evidence" toggle using existing `debug:true` (`evidence`) (20 min). Show retrieved chunks with BM25/embedding score and source URL side-by-side with the answer; one-click "Without RAG" shows the generic non-grounded template for contrast. Uses deterministic path only.

C. Canned multi-tool scenario button in ?demo=1 (30 min): "8 months pregnant, no car, storm tomorrow, 77096" fires prefetch `/ask/prefetch` + DEMO_SNAPSHOT data so risk, evac, NRI, emPOWER/medical, shelters (historical), insurance countdown tools all run from cache and the template answer cites each. Shows 5+ tools in one turn with 0 API cost and no network risk on stage. Also show `/ai/stats` cost estimate ("this answer: $0.00 - cached/templated").

D. (optional) Publish the eval scoreboard: render `docs/eval/latest.md` pass rate on Judge page as "Answers graded against sourced questions" - credibility, no cost.

## Suggested order for the remaining 4 h
1 (rain fell), 2 (polygons), A+C (agent trace + canned scenario), 5 + 9 (static link strips), then 4, 3 if time. Skip 8 unless a designer is free.
