# Cycle 20 research (Sun Oct 11, ~1:55 AM). 10 new ideas

Method: read README, CHANGELOG, business-case, flood-problems, cycle-12 research; probed every data source with curl at 1:45-1:55 AM. Rank = (safety impact x demo value) / effort. None of these is in the CHANGELOG. Only ideas 1-3 touch the backend. None calls Gemini at runtime. Existing conventions assumed: routers in `backend/app/routers`, helpers in `backend/app/services`, pages in `frontend/src/pages`, shared UI in `frontend/src/components`, strings in `frontend/src/i18n*`, meta{as_of,source,freshness} on data endpoints, tests in `backend/tests`.

Source probe key: tested OK = real response seen; FAIL = not usable.

## Ranked list

### 1. Coastal "Evacuation zone + storm surge" card (score highest)
- **Gap:** the app is rain/bayou only. Harris County's biggest hurricane risk (Seabrook, Kemah, La Porte, Clear Lake, Baytown) and the Texas ZIP-Zone A/B/C evacuation order are absent. Strong demo: "type Seabrook, get Zone A plus 'Cat 2 surge: under 3 ft above ground, Cat 3: over 6 ft'".
- **Data (tested OK):**
  - Evac zone: `https://services.arcgis.com/su8ic9KbA7PYVxPS/arcgis/rest/services/HurricaneEvac_Zones/FeatureServer/0/query` (HarrisCountyGIS, point query, inSR=4326, outFields `Zone,Zip5digit,Name,County`). Seabrook (-95.02,29.58) returned `Zip-Zone A`, ZIP 77586; Galveston returned `Zip-Zone Coastal`; Meyerland returned no features (so "not in an evacuation zone").
  - Surge: `https://mapservices.weather.noaa.gov/tropical/rest/services/tropical/StormSurgeRisk/MapServer/identify` with `layers=all:5` (Cat1), 9, 13, 17, 21 (Cat5 Image layers). `Raster.ClassName` returns "Less than 3 feet above ground", "Greater than 3 feet", "Greater than 6 feet", "Greater than 9 feet". Seabrook: Cat1 NoData, Cat2 under 3 ft, Cat3 over 6 ft. Meyerland: NoData for all (dry). Pass a `mapExtent` plus `imageDisplay` (400,400,96) or identify errors.
- **Owners:** `backend/app/services/evac.py` (new), `backend/app/routers/evac.py` (new, register in main.py), `frontend/src/components/EvacSurgeCard.tsx` (new, mounted in `pages/Prepare.tsx` or Home "This place"), i18n en/es.
- **Spec:**
  1. `GET /api/evac?lat&lon` returns `{zone, zip, county, evac_required_hint, surge:{cat1..cat5: class|null}, meta}`; 5 identify calls in parallel via `asyncio.gather`; cache 24 h (static data); any failure returns `null` fields, never "safe".
  2. Card shows zone, per-category surge depth and the line "Evacuate when your zone is called by Harris County/Judge; not official." Link `https://www.readyharris.org/` (200) and ready.gov hurricane page.
  3. Outside zone and all NoData: "Not in a storm-surge zone. Rain flooding can still happen" (links to the existing flood card).
- **Verify:** pytest with mocked httpx for Seabrook/Meyerland fixtures; curl the 2 live points above; demo_check +1 line; browser screenshot; manual: label says "approximate, NHC SLOSH worst-case, not a forecast".
- **Effort:** 1.5 h.

### 2. "How deep did it get here?" nearest USGS high-water marks
- **Gap:** the app says "flooded in Harvey" yes/no. Real street-level depth is the stronger story: "A surveyed Harvey mark 0.4 mi away: 3.2 ft above ground."
- **Data (tested OK):** `https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=180&States=TX` (Harvey, 2,298 marks statewide; 586 Harris County; 456 with `height_above_gnd`; fields `latitude_dd,longitude_dd,height_above_gnd,elev_ft,hwm_quality_name,survey_date,siteDescription`). `County=Harris` as a query param returned empty, so filter `countyName == "Harris County"` client-side. Event 342 (Beryl) returned 0 rows for TX; Ike is event 26. Crossings already use STN, so this reuses known data.
- **Owners:** `backend/app/services/hwm.py` (new; snapshot to `data/hwm_harvey_harris.json` via a one-off script so the demo does not depend on a live 2 MB call), `backend/app/routers/floodhistory.py` (add field `hwm_nearby` to the existing `/flood-history` response), `frontend/src/components/FloodHistoryCard` (extend).
- **Spec:**
  1. Load the snapshot, haversine to the nearest 3 marks within 1 mi with `height_above_gnd` not null and quality Good or better.
  2. Return `{distance_mi, height_above_gnd_ft, quality, survey_date, site}`; copy: "Nearest surveyed mark, X mi away, water reached N ft above ground. Marks are on riverine sites, not necessarily your house."
  3. Zero-height marks are shown as "0 ft (dry at mark)" and never as safe.
- **Verify:** unit test with Meyerland coords (expect at least one mark within 1 mi, else the "no mark nearby" text); check the snapshot count equals 456 +/- refresh; frontend build; screenshot.
- **Effort:** 1.25 h.

### 3. Galveston tide gauge "storm tide anomaly" chip (live)
- **Gap:** no coastal live data. Observed minus predicted water level is the standard surge signal.
- **Data (tested OK):** `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=water_level&station=8771450&date=latest&datum=MLLW&time_zone=lst_ldt&units=english&format=json&application=floodready` returned 2.972 ft at 02:12 today. Predictions: same URL with `product=predictions&range=24&interval=h` (tested OK). Also NHC `https://www.nhc.noaa.gov/CurrentStorms.json` (tested OK; currently lists an active storm, Isaias).
- **Owners:** `backend/app/services/tides.py` (new), extend `routers/status.py` source list and `routers/watch.py` (optional escalation: anomaly over 3 ft = "watch"), `frontend/src/components/GaugeChips.tsx` (add chip), i18n.
- **Spec:**
  1. Fetch latest observed and the prediction for the same hour; anomaly = obs - pred; cache 5 min; stale if the reading is older than 30 min (reuse existing freshness flags).
  2. Chip "Galveston tide: +0.4 ft above forecast" and, if NHC lists an active Gulf storm, a one-line "Active storm: name, classification" with link to nhc.noaa.gov.
  3. Anything missing shows "Unavailable", never 0.
- **Verify:** mocked-httpx pytest (normal, missing data, stale); live curl; `/api/status` row appears; build.
- **Effort:** 1.25 h.

### 4. Go-bag checklist + printable page + wallet card (client only)
- **Gap:** Prepare has a plan but no printable, offline kit list. High everyday demo value ("print it, put it on the fridge").
- **Data:** static content from ready.gov/kit (tested OK, 200) and ready.gov/pets (OK). cdc.gov hurricane pets page returned 403 to curl, so do not cite it.
- **Owners:** `frontend/src/components/GoBag.tsx` (new), `frontend/src/pages/Prepare.tsx` (mount), `frontend/src/styles` print CSS, i18n en/es (vi/zh/ar fall back, state it), `data/knowledge` card optional.
- **Spec:**
  1. Checkbox list grouped (water 1 gal/person/day x 3, meds 3-day, documents in a bag, chargers, flashlight, pet items, baby items) with checks stored in localStorage (try/catch).
  2. "Print" button uses `@media print` to render a one-page list; "Wallet card" prints a business-card-size block: household names, medical needs, out-of-state contact, 911/211/311 (211 and 311 already in the app).
  3. Household profile (existing) prefills pet and medical lines.
- **Verify:** build; browser print preview screenshot; keyboard-only tick test; no network calls (offline).
- **Effort:** 1.5 h.

### 5. Storm-season calendar pack (.ics) (client only)
- **Gap:** only one insurance .ics exists. Add recurring reminders: June 1 hurricane-season prep, Sep peak, test the go-bag every 6 months, 30-day flood-policy wait date, "check gauges" before forecast rain.
- **Data:** none; RFC 5545 generated in browser. Reuse the insurance .ics helper in the Prepare code.
- **Owners:** `frontend/src/lib/ics.ts` (extend existing helper), `frontend/src/components/SeasonReminders.tsx` (new), Prepare page mount, i18n.
- **Spec:**
  1. One button downloads a single .ics with `RRULE:FREQ=YEARLY` events (Jun 1, Aug 15, Sep 10, Nov 30 season end) and VALARMs.
  2. A "Add to Google Calendar" link per event using `calendar.google.com/calendar/render?action=TEMPLATE` URLs.
  3. Text says "reminders are generic, not alerts."
- **Verify:** unit test that output starts `BEGIN:VCALENDAR`, CRLF line endings, UIDs unique; import the file into macOS Calendar or Google Calendar and screenshot.
- **Effort:** 0.75 h.

### 6. Insurance-claim photo log with offline storage (client only)
- **Gap:** Recover has a tracker but no evidence capture. Documenting damage before cleanup is the top claim advice (fema.gov documenting page returned 403 to curl; cite floodsmart.gov / ready.gov instead, re-verify in browser).
- **Data:** none; browser camera input + IndexedDB.
- **Owners:** `frontend/src/components/DamagePhotoLog.tsx` (new), `frontend/src/lib/idb.ts` (new, tiny wrapper), `frontend/src/pages/Recover.tsx`, service worker untouched.
- **Spec:**
  1. `<input type=file accept=image/* capture=environment multiple>`; downscale to 1600 px via canvas; store blob + room tag + note + timestamp + optional lat/lon in IndexedDB; nothing leaves the device (say so).
  2. Grouped by room, delete per photo, "Export" zips nothing: opens a printable page (photos + notes + time) to save as PDF for the adjuster.
  3. Storage failure shows a visible message, never silent.
- **Verify:** Playwright with a fixture image: add, reload, still present, export view renders; build; check quota error path with a mocked throw.
- **Effort:** 1.75 h.

### 7. "What changed since your last visit" digest (client + existing endpoints)
- **Gap:** returning users get no diff. Demo value is good for storm night.
- **Data:** existing `/risk`, `/alerts`, `/outlook`, gauge status endpoints. No new source.
- **Owners:** `frontend/src/lib/lastVisit.ts` (new), `frontend/src/components/ChangeDigest.tsx` (new), `pages/Home.tsx` (mount above hero), i18n.
- **Spec:**
  1. On each Home load store a small snapshot in localStorage `{ts, alertCount, topAlert, outlookCategory, worstGaugeStage}` (try/catch).
  2. Next visit compares and lists up to 4 plain lines: "WPC outlook rose from Marginal to Slight", "New: Flood Watch for Harris", "Brays Bayou at Main: Action to Normal", else "No change since 6 h ago".
  3. Dismiss button; never show a change when either side is missing (no fake "no change").
- **Verify:** unit test the pure diff function with 6 fixtures; browser test by editing localStorage; build.
- **Effort:** 1.25 h.

### 8. Detention basin and storm-drain neighbor explorer
- **Gap:** F-series accountability and "where does the water go". Shows the nearest HCFCD detention basins (name, watershed, unit) on a map layer.
- **Data (tested OK):** `https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services/HCFCD_Detention_Basins/FeatureServer/0/query` (polygon layer, ArcGIS point+distance query worked; fields WATERSHED, COMMENTS, UNIT, Name). Bond-funded set: `HCFCD_Bond_Detention_Basins_Bond/FeatureServer` (listed, not queried). Houston 311 recent-requests feature server returned "service not started", so skip 311 data.
- **Owners:** `backend/app/routers/civic.py` (add `/civic/detention?lat&lon&r=3000`), `backend/app/services/arcgis.py` or the existing helper for ArcGIS queries, `frontend/src/pages/Civic.tsx` list plus Leaflet layer.
- **Spec:**
  1. Return up to 5 basins within 3 km with name, watershed, distance and centroid (outSR 4326).
  2. UI: list plus map pins, caption "Detention basins hold stormwater; nearby basins do not guarantee your street will not flood."
  3. Empty state names the source and says no basin within 3 km.
- **Verify:** curl with Meyerland point (expect at least one hit); mocked test; screenshot.
- **Effort:** 1.5 h.

### 9. Pet and livestock safety card (client, static content)
- **Gap:** pets block evacuation choices; zero pet content today.
- **Data:** ready.gov/pets (tested OK, 200). Local sources to link: readyharris.org (OK). Do not cite CDC (403 to curl).
- **Owners:** `data/knowledge/pets.md` (new RAG card, deterministic retrieval picks it up), `frontend/src/components/PetCard.tsx` (new), Prepare page, household profile field `pets` (existing profile code), i18n en/es.
- **Spec:**
  1. Card: bring pets in early, ID tags/microchip, carrier, 3-day food and water, vaccine records, never leave pets tied; shelters often refuse pets so plan a pet-friendly option ahead; livestock: move to high ground before water rises.
  2. Pet toggle in the household profile adds items to the go-bag (idea 4).
  3. Each claim links to ready.gov/pets; no invented shelter names or phone numbers.
- **Verify:** `/ask` deterministic route test ("what do I do with my dog in a flood") without Gemini (keys blanked in conftest); build.
- **Effort:** 0.75 h.

### 10. Embeddable widget + underpass QR poster
- **Gap:** B2B value for the business case (partner sites such as schools, HOAs, apartments) and a print-ready physical-world demo.
- **Data:** none new; reuses `/api/risk`, `/api/crossings`. QR library already in the bundle (Judge page).
- **Owners:** `frontend/src/pages/Embed.tsx` (new, route `/#embed?lat&lon`), `frontend/src/pages/Judge.tsx` (add "poster" button) or a `components/CrossingPoster.tsx` (new), `deploy/Caddyfile` only if frame headers need changing (check `X-Frame-Options`).
- **Spec:**
  1. `/#embed?zip=..` renders a compact card (risk badge + live alert count + link) and a copyable `<iframe>` snippet on the Judge page.
  2. Poster: pick any of the 128 crossings, print an A4 page "Turn around, don't drown" with crossing name and a QR to `/#drive?crossing=<id>`.
  3. Poster uses only bundled data, so it works offline.
- **Verify:** load the iframe in a local test HTML page; print preview screenshot; scan the QR with a phone or `zbarimg` if present.
- **Effort:** 2.0 h (trim to the poster only if time is short).

## Considered and rejected

| Idea | Why |
|---|---|
| CenterPoint outage map | FAIL. The ArcGIS `Outage/OUTAGE_TRACKER_OEP_ALL` service returns 404/redirect; `centerpointenergy.com/en-us/outage-tracker` returns 404. No public feed found. Link out only. |
| School closures feed | No structured free feed found (HISD site loads but offers no API). Link out only. |
| Houston 311 deep integration | Recent-requests service "not started"; archives MapServer live but last updated 2025/06/25 and not real-time. Only a `tel:311` link and the existing copyable message are safe. |
| NHC surge raster tiles for a map layer | Identify works; tile overlays add effort for little extra safety value. Use idea 1. |
| Overpass vet lookup | Overpass returned 406 to curl (needs a User-Agent); skip. |
| Sign-language video, buddy check-in | No verified free content/host in the time left. Buddy check-in could be an `sms:` deep link inside idea 4 if time remains. |
| Neighborhood risk comparison | Needs a ZIP-level risk dataset not already bundled; risk of an unsupported ranking. |

## Execution order for a 2-agent split
- Agent A (backend-leaning): 1, 3, 2 (shared test fixtures; about 4 h total, so choose 1 and 2 first).
- Agent B (frontend-only): 4, 5, 7, then 6 or 9.
- Skip 8 and 10 unless there is slack before the 11 AM freeze.
- Every idea: run the pytest suite, `demo_check.py --front`, a frontend build, and add the en/es strings; do not run live-Gemini evals (policy from the quota incident).
