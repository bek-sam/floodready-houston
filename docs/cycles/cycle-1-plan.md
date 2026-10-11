# Cycle 1 Plan (Sat Oct 10 2026)

## 1. Bugs and risks found by reading code
1. `backend/app/services/route.py:41-43,89` — if OSRM fails the route is a straight line, yet a route with no hazards still returns `verdict:"safe"`. Wrong fact in a safety app. Fix: when `warnings` has the fallback, return verdict `"caution"` and say "route unavailable, check manually".
2. `backend/app/services/watch.py:36` — `severity in ("Severe","Extreme")` makes a plain Flood Watch a "warning" (watch alerts are usually Severe), so push and Watch screens over-alarm. Fix: decide by `event` containing "warning" only.
3. `backend/app/services/gauges.py:43` — last observation is used with no age check, so a stale reading shows as current. Fix: if `validTime` is older than 6 h, set status `unknown`.
4. `backend/app/ai/graph.py:235-236` — Gemini answers may cite any URL it writes; `allowed` (line 232) is computed but unused. Fix: `sources = [u for u in found if u in allowed or u in tool_sources]`, else top allowed.
5. `backend/app/ai/graph.py:14-16,257` — disclaimer exists only for en/es; vi/zh/ar/ur answers end in English. Fix: add vi/zh/ar strings ("Call 911" kept).
6. `frontend/public/sw.js:5` — `/api/route-check/demo`, `/api/risk`, and `/api/alerts` are not cached, so the offline demo has no routes or last-known risk. `/api/knowledge` is dead. Fix: add route-check/demo, risk, shelters; bump `SHELL` to v2.
7. `backend/app/services/insurance.py:7-8` — a purchase after Nov 30 compares against the same year's season end, so the "after this season" message is wrong in December. Fix: use next year's Nov 30 when `pd > Nov 30`.
8. `backend/app/services/alerts.py:5-13` — alerts with no `warnings` key on failure of a parsed-but-empty response; `description` is passed in full (several KB) into the agent and Watch payloads. Fix: truncate to 600 chars.

## 2. Ranked backlog (score = impact × demo ÷ effort, 1-5 scales)
| # | Item | I | D | Effort | Score |
|---|---|---|---|---|---|
| 1 | Bugs 1+2+3 (wrong-fact fixes) | 5 | 4 | 0.5h | 40 |
| 2 | Shelter finder (`/shelters`) + UI | 5 | 5 | 1.5h | 16.7 |
| 3 | WPC rainfall outlook badge (`/outlook`) | 4 | 5 | 1h | 20 |
| 4 | Post-flood money-safety + mold knowledge cards (RAG + Recover) | 4 | 4 | 1h | 16 |
| 5 | Bugs 4+5 + new AI cues | 3 | 3 | 0.5h | 18 |
| 6 | Insurance `.ics` download (client-side) | 3 | 4 | 0.5h | 24 |
| 7 | Printable go-bag | 3 | 3 | 1.5h | 6 |
| 8 | Check-in share link + 211 link-outs | 3 | 3 | 1h | 9 |
| 9 | Bug 6,7,8 | 2 | 2 | 0.5h | 8 |

## 3. CHOSEN for this cycle (four parallel lanes, no shared files)

### A. backend/ (excl. app/ai) — outlook, shelters, bug fixes 1,2,3,7,8
Files: new `services/shelters.py`, `services/outlook.py`, `routers/shelters.py`, `routers/outlook.py`; edit `main.py` includes, route.py, watch.py, gauges.py, insurance.py, alerts.py.
Contract additions (add to CLAUDE.md table via lead):
- `GET /api/shelters?lat&lon&pet_friendly=false&limit=10` returns `{shelters:[{name,address,county,status:"Open"|"Pending"|"Full"|"Closed",capacity,occupancy,pet_friendly:bool,lat,lon,distance_mi}], any_open:bool, source:"https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Evacuation_Shelters/FeatureServer/0", note, warnings?}` sorted by distance. Query the layer through `arcgis.full_layer("shelters", url)` (snapshot fallback). If no shelter is Open, set `any_open:false` and note "No shelters are open right now; this list is a directory. Call 211 or 311; in danger call 911." Never present Pending/Closed as open.
- `GET /api/outlook?lat&lon` returns `{day1:{category:"None"|"Marginal"|"Slight"|"Moderate"|"High", label}, source:"https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer", note}`. Run a point-in-polygon `/query` (geometry=lon,lat; inSR=4326) on the "Excessive Rainfall Day 1" layer. Discover the layer id and category field first via `...MapServer?f=json`. No intersection means "None". On failure return `day1:null` with `warnings`.
Acceptance: `curl '/api/shelters?lat=29.76&lon=-95.37'` returns 200 with a `shelters` array and `any_open`. Airplane-mode test (`HTTP_TIMEOUT` hit) returns 200 with a snapshot or an empty list, not 500. `curl '/api/outlook?lat=29.76&lon=-95.37'` returns 200. `pytest`: OSRM down gives verdict != "safe"; a Flood Watch Severe alert gives level "watch".

### B. data/ — post-flood money-safety + mold cards, shelter snapshot
- New `data/knowledge/post-flood-money-safety.md`, one `##` heading per topic, each fact followed by its URL, in the existing card style (read `post-flood-safety.md` first). Content with sources only from the research file:
  - Scams: TX AG says contractors take upfront payment, and price gouging is barred after a governor's disaster declaration; report line (800) 621-0508. https://www.texasattorneygeneral.gov/news/releases/attorney-general-paxton-warns-disaster-scams-following-texas-floods
  - Flood cars: Cox estimated up to ~500,000 Harvey cars totaled; NICB says titles are sometimes washed. Offer a "check the VIN before buying" action. https://www.foxnews.com/us/after-hurricane-harvey-what-will-happen-to-the-hundreds-of-thousands-of-flooded-cars
  - Renters: 2021 TX law requires landlords to disclose floodplain status and floods in the last 5 years (leases from 1/1/2022); send repair requests in writing; Harris County Attorney 713-755-6065. https://abc13.com/amp/post/flood-warnings-texas-rental-law-landlords-renters/11399135/ and https://www.fox26houston.com/news/assessing-the-flood-damage-as-renters. Do not state the 30-day termination rule as fact unless the statute is verified.
  - FEMA denial: Harvey, 41% of 895,342 Texas registrants approved and 31% ineligible; appeal window was 60 days in Harvey (tell users to confirm the current window at fema.gov). https://govtech.com/em/disaster/-disaster-victim-actvists-concerned-about-femas-fairness-transparency.html
- Append a "Mold" section to `post-flood-safety.md`: Houston focus groups (31 residents) found cost led to long exposure; Houston-3H (347) linked mold to allergic symptoms for up to a year. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9198619/
- Snapshot `data/shelters.json` (GeoJSON features from the layer's `f=geojson` query, `outSR=4326`) as the offline fallback, loaded by backend via `load_json("shelters.json")`.
Acceptance: files exist; every fact line has an `http` URL; `rag.search("price gouging contractor")` (AI lane's test) returns the new chunk.

### C. backend/app/ai/ — bugs 4,5 + new cues
- Fix `graph.py` source filter and add vi/zh/ar disclaimers (keep "911").
- Add CUES in `graph.py` (scam/gouging/contractor, mold, vin/used car, denied/appeal) pointing to the new card (`post-flood-money-safety.md`); add `shelter` intent plus a `get_shelters` tool in `tools.py` that does `try: from app.services.shelters import get_shelters` and returns `{"error":...}` if absent. Backend (lane A) exposes `async get_shelters(lat, lon, pet_friendly=False, limit=5) -> dict` in `services/shelters.py` as the same dict as the endpoint.
Acceptance: `POST /api/ask {"question":"A contractor wants cash upfront","lang":"en"}` with no GEMINI key returns an answer citing texasattorneygeneral.gov and "Call 911"/"Not official guidance". An answer with `lang:"vi"` ends in Vietnamese. `pytest` for the AI folder passes.

### D. frontend/ — Shelters panel, outlook badge, .ics, offline cache
- Recover: "Find a shelter" card calling `api.shelters`; shows status chips, a pet-friendly toggle, a "no shelters open, call 211" state when `any_open` is false, and the source link. Add `api.shelters` and `api.outlook` plus their types to `api.ts` (matching A exactly).
- Home/Watch: "Tonight's rain risk: Slight" badge from `/outlook`, with the source link, hidden when `day1` is null.
- Prepare (insurance countdown): "Add to calendar" button building an `.ics` Blob client-side from `Countdown.effective_date` (no endpoint needed).
- `sw.js` (bug 6): cache shelters, outlook, route-check/demo, risk; bump cache names.
Acceptance: `npm run build` passes; with the backend stopped, the shelter card shows a friendly offline message (no crash); `.ics` file opens with the correct date; the badge is hidden when the endpoint fails.

Dependencies: D codes against the contract above and tolerates 404/503. A and B are independent (B's snapshot is optional for A). C depends only on the `get_shelters` signature, guarded by a try/except.
