# Verification of problem groups A and B (drivers; maps give false safety)

Date: 2026-10-11. Tested against the running backend (:8000) and frontend (:5173), plus code review. No app code was edited. Scripts: `scratchpad/e2e/verify-AB/*.py` (Playwright, 390x844 mobile viewport, localStorage seeded as specified). One `/ask` call used.
Test places: Meyerland (29.6876,-95.4583), Seabrook (29.564,-95.025), Addicks (29.7869,-95.644), Downtown (29.7604,-95.3698).

Verdict key: SOLVES = a user can act and harm is reduced. PARTIAL. INFORMS ONLY. NOT ADDRESSED. NOT APP-SOLVABLE.
All "coverage" claims below are compared with `docs/cycles/cycle-35-coverage.md`, which counts A1, A3-A9 and B1-B3, B6, B7, B9-B11 as REDUCES.

## Summary table

| ID | Verdict | Claimed (cycle 35) | One-line reason |
|---|---|---|---|
| A1 | PARTIAL | REDUCES | Route check and watch work. Real-time "avoid" needs a HIGH crossing and an active alert, and conditions are read only at the route midpoint |
| A2 | INFORMS ONLY | INFORMS | Harris-vs-Dallas stat is only in `data/knowledge/driving-in-floods.md` (reachable via Ask). Not shown on Drive |
| A3 | PARTIAL | REDUCES | Personal verdict + poster exist, but the message is the same "Turn around, don't drown" slogan. No evidence it changes behavior |
| A4 | PARTIAL | REDUCES | 128 crossings with sources, but data errors (see bugs 4, 5) and no live signal per crossing |
| A5 | PARTIAL | REDUCES | Mapped and public with sources. Coverage is the central Houston area; a Seabrook-origin route found only downtown spots |
| A6 | PARTIAL | REDUCES | App cannot install sensors or barricades. Crowd reports (`barricade_missing`) feed route checks but are unauthenticated and spoofable |
| A7 | PARTIAL | REDUCES | Pre-trip check, watch push, SMS alerts, QR poster. Nothing warns a driver already on the road, and no alternative route is offered |
| A8 | PARTIAL | REDUCES | Same as A1. Avoids named crossings but gives no detour |
| A9 | PARTIAL | REDUCES (was INFORMS) | Parking check works and gives a higher-ground spot. False "no flags" at the Addicks pool point |
| B1 | SOLVES | REDUCES | FEMA zone shown next to Harvey result. Zone matched FEMA at all 4 points. One false negative (bug 3) |
| B2 | SOLVES | REDUCES | "Low-risk zone, but this ZIP has 74 NFIP claims since 2017" appears for a ZIP 77002 address. Needs a ZIP in the saved label |
| B3 | SOLVES | REDUCES | Zone X copy says "does NOT mean safe". Summary shows "Elevated exposure" for Downtown and Addicks despite Zone X |
| B4 | INFORMS ONLY | INFORMS | One line in the "What the FEMA map misses" list. The "rearview mirror" story is only in the knowledge base |
| B5 | NOT APP-SOLVABLE | INFORMS | Map timing is FEMA's. The UI says nothing about draft status; only Ask knowledge does |
| B6 | SOLVES | REDUCES | The mobile risk card at 390 px is clear. It replaces the phone-hostile MAAPnext viewer |
| B7 | INFORMS ONLY | REDUCES | "Shift the storm" is two hard-coded numbers (~3,600 vs 13,000+) and a fixed-width bar. It is not a simulation and is not about the user's address |
| B8 | INFORMS ONLY | INFORMS | `low_ground` is null at every point tested (9 points). Rain card is a model estimate |
| B9 | PARTIAL | REDUCES | A "questions to ask landlord or seller" list and an Addicks flag. The only letter generator is for buyout tenants, not a pre-lease disclosure request |
| B10 | PARTIAL | REDUCES | Watch status, SMS and push endpoints work. Push could not be delivered in headless. "Storm mode" banner showed with no alerts (bug 7) |
| B11 | INFORMS ONLY | REDUCES | Officials and floodplain administrator with phone numbers are correct. Rules differ by jurisdiction regardless of the app |

Counts: SOLVES 4 (B1, B2, B3, B6), PARTIAL 10 (A1, A3-A9, B9, B10), INFORMS ONLY 5 (A2, B4, B7, B8, B11), NOT APP-SOLVABLE 1 (B5), NOT ADDRESSED 0. Cycle 35 credits 14 of these 20 as REDUCES. This audit supports 4 firm and 10 conditional.

## Per-problem detail

### A1, A8 (driving into water; drownings in vehicles)
- Features: `POST /route-check` (`backend/app/services/route.py:90-190`, router `routers/route.py`), Drive page (`frontend/src/pages/Drive.tsx:99-110`, result card line 193+), watch/push (`services/watch.py:42`), SMS.
- Tests:
  - Demo "Allen Parkway underpass" route: `caution`, 4 named hazards (Underpass at 2900 Allen Parkway; Louisiana St. at North of Franklin St; Fannin St. bridge (Harvey HWM); San Jacinto Bridge). With `?simulate=storm` it returns `avoid`. In the UI (`/?demo=1#drive`, sample plus Simulate toggle) the card read "Avoid this route - Simulated", listed all 4 with source links, a poster button and Read aloud.
  - Meyerland to 1001 Fannin St (typed address, UI and API): `safe`, no hazards, copy "No known flood-prone crossings on this route" (the wording is honest).
  - Meyerland to Downtown, storm sim: only `caution` (one medium crossing, Walker St.). Seabrook to Downtown: `caution`, 2 spots.
  - Asked "Is it safe to drive through 6 inches of standing water?" (1 `/ask` call, tools get_risk and get_alerts, Gemini): "No ... take another route". Correct but generic.
- Gaps:
  - `avoid` needs `hazards and high and active` (`route.py:168`). A route with only MEDIUM crossings (85 of 128) stays `caution` even in a real flood warning.
  - Live conditions are checked at the route midpoint only (`route.py:~136`). A long route's far end is not checked.
  - If an NWS flood warning is active but no crossing is within 75 m, the verdict is still `safe` and the message does not mention the warning.
  - 75 m buffer is 2D: an elevated freeway above a listed underpass is flagged, and a different road beside it is not.
  - No alternative route or detour is suggested.
- Verdict: PARTIAL. A trip planner that names real spots is useful, but it only protects users who check, and the "avoid" threshold is narrow.

### A2 (Harris County worst for vehicle deaths)
- Only text: `data/knowledge/driving-in-floods.md` (77% line, Dallas comparison). Nothing in the UI. Not app-solvable as a harm. INFORMS ONLY.

### A3 (slogan has no measurable effect)
- Features: personal route verdict (above), underpass poster with QR (`components/poster/PosterSheet.tsx`; tested, renders "Turn around, don't drown", location "Underpass at 2900 Allen Parkway", Print button, QR to `#drive/to=lat,lon`).
- Gap: the poster and verdict copy lean on the very slogan the evidence says does not work. The personal verdict is the new part, and only helps after the user opens the app. PARTIAL.

### A4, A5 (same underpasses kill; crossings unmapped)
- Features: `/crossings` (128 features, 43 high, 85 medium, all have `sources`), Drive map with markers and list (`Drive.tsx:231-262`), crossings in route and watch (`crossings_nearby`).
- Test: `/crossings` returned 128 features with `meta.freshness:"snapshot"`. The map renders all of them on a 390 px screen (screenshot `verify-AB/drive0.png`).
- Data issues:
  - `x126` is named "San Jacinto Bridge (Harvey HWM)", plotted at (29.7630,-95.3574) in downtown, and its reason says the water body is "(gulf of Mexico)". 6 features carry that label. Wrong waterbody and probably a wrong name.
  - `x119` "Fannin St. bridge at Buffalo Bayou" is plotted at lon -95.3579. The Census geocode of 1001 Fannin St is lon -95.3640, so the marker is about 0.5 km east of Fannin. Either the name or the point is off.
  - Names such as "Louisiana St. at North of Franklin St" come from the KPRC list and read oddly.
  - 54 of the points are Harvey high-water marks, not known driver hazards. They raise the count of "flood-prone spots" on a route without evidence the road floods.
- Verdict: PARTIAL for both. Real, sourced, and useful; accuracy of some points is doubtful, and there is no per-crossing live state.

### A6 (incomplete physical warnings)
- App-side: reports of kind `water_over_road`, `barricade_missing`, `flooded_road`, `stalled_vehicles` (`routers/reports.py:15-40`) count as hazards on routes for 6 h (`route.py:42-64`), with Still there / Cleared votes.
- Test that shows a weakness: I posted one anonymous `water_over_road` 10 in report on an isolated test road. The route verdict changed from `safe` to `avoid` ("Avoid this route ... community report of 10 in of water"). Two anonymous "Cleared" votes then made it `safe` again. There is no auth, rate limit or reputation. (Report is cleared and expires in 6 h.)
- Also: the contract says reports last 24 h, but code uses 6 h (`REPORT_MAX_AGE_H = 6`).
- Verdict: PARTIAL. It can only supplement official sensors.

### A7 (drivers go around barricades; warn them before the water)
- Features: pre-trip check, watch push (5-min loop; `/push/vapid-public-key` works), `/sms/simulate`, poster at the site.
- Tests: `/watch/status?simulate=storm` for Meyerland returned `warning` with three simulated gauge reasons and "avoid low roads and underpasses". For a Downtown place it returned `warning` and `crossings_nearby: 13`. SMS: "77096" and a street address both return a risk summary with "Call 911 if in danger". "ROUTE 77096 to 1001 Fannin" was not parsed as a route command and just returned the ZIP summary (SMS has no driving check). In headless Chrome notifications are blocked, so push delivery was not tested.
- Gaps: place-based, not route- or time-of-trip-based. No in-car alert. `crossings_nearby` is shown but does not by itself raise the level. PARTIAL.

### A9 (vehicle losses)
- Feature: "Where should I park?" (`GET /parking/check`, `services/parking.py`; card `components/parking/ParkCard.tsx`, shown on Drive).
- Tests: Meyerland `move` (FEMA AE, Harvey true), with a spot 5.8 ft higher, 400 m away and a Maps link. Downtown `move` (2 crossings within 300 m). Seabrook `move` (AE, higher ground 6.4 ft). UI at Meyerland: "Consider moving your car to higher ground before heavy rain ... Add a 'move car' reminder", with limits text and 911 line.
- False reassurance: Addicks point returned `no_flags` (zone X, Harvey false), although it is in the reservoir pool area (bug 3).
- Verdict: PARTIAL. It is the one feature in A that gives a concrete protective action, but the "higher ground" is a 400 m elevation sample, not a verified safe lot.

### B1 (most flooding outside FEMA zones)
- Features: `/risk` (`routers/risk.py`, `services/risk.py`), Home summary (`pages/Home.tsx`, `components/home/SummaryHero.tsx`), `/harvey/extent`, `/hwm`, `/flood-history`.
- FEMA check: queried NFHL layer 28 directly at all 4 points. App zone matched each time: Meyerland AE, Seabrook AE, Addicks X (AREA OF MINIMAL FLOOD HAZARD), Downtown X.
- Home (390 px): Meyerland "THIS PLACE: High exposure - Flooded in Harvey and in a FEMA high-risk zone"; Downtown "Elevated exposure - Major flooding at the nearest gauge in Hurricane Harvey" with FEMA Zone X shown; HWM for Meyerland returned 5 marks (nearest 5.8 ft above ground, 0.56 mi, Cliffwood Court near Brays Bayou); Seabrook Harvey = null with "no Harvey extent data" (honest, not "dry").
- Bug 3 (Addicks) is the exception. Verdict: SOLVES.

### B2 (low-risk zones file many claims)
- Feature: Rent/buy decision card (`components/RentBuy.tsx:107`) with `GET /zip-insurance`.
- Test (UI, saved label "1001 Fannin St, Houston, TX 77002", zone X): "Low-risk zone, but this ZIP has 74 NFIP claims since 2017. ... Typical premium: about $1,828 a year". API `/zip-insurance?zip=77096`: 6,482 claims total, 2,610 since 2017, 4,537 policies, median premium $1,501. The ">25% of claims are in moderate/low zones" stat is not on screen (only in knowledge).
- Gap: with no ZIP in the saved place (Meyerland seed), the card says "Search an address with a ZIP code". Verdict: SOLVES.

### B3 ("not in a flood zone" misleads)
- Home copy for zone X: "Outside the highest-risk zone. That does NOT mean safe: nearly half of the homes Harvey flooded ... were outside the 100- and 500-year floodplains". The exposure level can be Elevated even in X (Downtown, Addicks). SOLVES.

### B4, B5 (outdated maps; new maps years away)
- Only the one fact "Draft FEMA maps use rainfall rates more than 30% higher than the 2007 maps still in effect" (`risk.py:68`), listed under "What the FEMA map misses". No "not final / not regulatory / 2-3 years" text in the UI. The draft status is in `data/knowledge/outdated-maps-and-maptool-status.md` and only reachable through Ask.
- B4 INFORMS ONLY. B5 NOT APP-SOLVABLE (and under-informed).

### B6 (draft viewer is unusable on phones)
- Verified at 390 px: Home and Drive render a color/word-coded badge (High exposure, Normal) with text, not "shades and dots". SOLVES.

### B7 (storm track matters)
- `pages/Replay.tsx:236-258` (`ShiftCard`): `homes = shifted ? '13,000+' : '~3,600'`, bar width 100% or 28%. Rice published numbers, with source links labelled "published". It is not a simulation and has no relation to the user's place. The replay itself (gauge series by event, play control, 2D/3D) works. INFORMS ONLY (cycle 35 counts it as REDUCES).

### B8 (drain and sheet-flow flooding)
- `/risk` `low_ground` was null for 9 points with note "no gauge datum available to compare ground elevation with flood-stage elevation" (`services/risk.py:47`). So the plan's "low-ground flag" never fires. Rain card (`/rain24`) is a model estimate. Harvey layer note says street flooding is not in it. INFORMS ONLY.

### B9 (no disclosure to buyers and renters)
- Home "Renting or buying here?" has a list of questions for the landlord or seller, the Addicks/Barker flag and an insurance 30-day note. The `TenantLetter` component (`components/TenantLetter.tsx`) and the "To the buyout program administrator" letter are for displaced renters or buyouts, not a pre-lease flood-history request. The checklist is not copyable as a letter. PARTIAL.

### B10 (people caught unaware)
- Watch/alerts page (`#alerts`) shows per-place level, crossings nearby and Check a route. Backend watch/push/SMS tested above. Push permission and delivery cannot be proven in headless. PARTIAL.

### B11 (jurisdiction rules differ)
- `/civic` returns commissioner, council member and floodplain administrator with phone and address. Meyerland: Precinct 1, council district C (Abbie Kamin), Houston floodplain administrator. Seabrook: Precinct 2, no council seat, Seabrook floodplain administrator (phone 281-291-5638). The jurisdiction line on Home is correct ("City of Houston", "Seabrook (limited purpose area)"). This tells users whom to call; it does not change the rules. INFORMS ONLY.

## Bug list (ranked)

1. **Single anonymous report flips a route to AVOID; two anonymous "Cleared" votes cancel a real one.** Repro: `POST /api/reports {lat,lon,kind:"water_over_road",depth_in:10}` at a point on a route, then `POST /api/route-check` for that route returns `avoid`; `POST /api/reports/{id}/vote {"still_there":false}` twice returns `cleared:true` and the route returns to `safe`. No auth or rate limit. Files: `backend/app/routers/reports.py:31-60`, `backend/app/services/route.py:17-64, 125-160`.
2. **"Avoid" is too hard to reach, and `safe` ignores active alerts.** `route.py:168` requires a high crossing plus active conditions. Meyerland to Downtown with `simulate=storm` gives `caution`. With a real flood warning and no crossing within 75 m, the verdict is `safe` and the message omits the warning. Conditions are read at the route midpoint only.
3. **Addicks reservoir-area point shows "Not in Harvey's mapped extent" and parking `no_flags`.** Repro: `GET /api/risk?lat=29.7869&lon=-95.644` returns `harvey.flooded:false`, `elevation_ft:92.1`, while the nearby Addicks gauge `impact.harvey_crest_ft` is 109.09 (and `/parking/check` returns `no_flags`). The app has the data to contradict the chip but does not use it. Home also shows the chip beside the reservoir-area flag, which is mixed messaging.
4. **Wrong data in `data/crossings.geojson`.** `x126` "San Jacinto Bridge (Harvey HWM)" reads "(gulf of Mexico)" and is plotted in downtown; 6 features carry the "gulf of Mexico" label. `x119` "Fannin St. bridge" is plotted about 0.5 km east of Fannin St (lon -95.3579 vs -95.3640). Both appear in the Allen Parkway demo route output.
5. **54 of 128 "flood-prone crossings" are Harvey high-water marks, not known driver hazards**, yet they are counted in route messages ("crosses 4 known flood-prone spot(s)").
6. **`low_ground` is always null** (`services/risk.py:47`); B8 is not delivered.
7. **"Storm mode: refreshing every 1-2 min" shown on every card** while the places had no alerts and gauges were normal (`GET /api/status` `storm_mode: true`). The flag is global (`freshness.mark_storm`, 180 s hold) and I could not isolate the trigger. It can confuse users and wastes the 90 s TTL cap.
8. **B7 "Shift the storm" is a static two-state toggle** (`pages/Replay.tsx:236-258`), presented as a simulation in the plan.
9. **SMS has no route or driving command**; "ROUTE 77096 to 1001 Fannin" returns the ZIP summary.
10. **Report window mismatch:** contract says 24 h, code `REPORT_MAX_AGE_H = 6` (`route.py:14`), and the UI says "last 6 hours". Update the contract doc.
11. **B4/B5 draft-map status and the 25% claims stat are not in the UI**; only in `data/knowledge`.
12. **Test residue:** two watch places ("verifyAB Meyerland", "verifyAB downtown") and one cleared report ("verifyAB test") remain in the dev DB.
