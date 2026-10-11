# Verification of problem groups C (insurance) and D (warnings), 2026-10-11

Method: read code, called the running API (localhost:8000), drove the UI with Playwright at 390 px (scripts in `scratchpad/e2e/verify-CD/`), and cross-checked numbers against OpenFEMA and api.weather.gov directly. No real push or SMS was sent. 0 `/ask` calls used. Test side effects: 4 `Place` rows (Meyerland, Seabrook, Downtown, "SC") and a few fake-phone SMS rows (+1555555xxxx) were created in the dev DB.

## Verdict table

| ID | Verdict | One-line reason |
|---|---|---|
| C1 | PARTIAL | Harvey 36% fact, ZIP claims, "Should you buy here?" card. Informs and nudges; cannot sell a policy. ZIP card missing when the place label has no ZIP. |
| C2 | INFORMS ONLY | The 92% quote exists only in `data/knowledge` (Ask). No UI surface. No address-level uninsured estimate. |
| C3 | PARTIAL | Countdown date math correct; exceptions partly listed. Manual, not tied to a forecast. Frames "season end" as Nov 30. |
| C4 | INFORMS ONLY | Real OpenFEMA ZIP premium range (good) but no Risk Rating 2.0 change/trend for the address. CSFI figures only in Ask. |
| C5 | NOT APP-SOLVABLE | No NFIP affordability program exists. "Ways to pay less" is generic levers, correctly labelled. |
| C6 | INFORMS ONLY | Nothing on price trajectory in the UI; only a one-time snapshot premium. |
| C7 | PARTIAL | Address-level "low-risk zone but ZIP has N claims", Harvey flag, "lower risk is not zero". 9M vs 14.5M only in Ask. |
| D1 | PARTIAL | Replaces the gage map with a real notification path (NWS point alerts + gauges + crossings + reports). Only 36 gauges metro-wide; no street ponding. |
| D2 | PARTIAL | Web push is one toggle with no account. SMS "ALERTS ON" is a no-op (no sender exists). iOS needs Home Screen. Real delivery not verified. |
| D3 | PARTIAL | Alerts are point-in-polygon (verified equal to NWS point query), not county. Route check samples only the midpoint. |
| D4 | PARTIAL | Rain24, WPC outlook, gauges, push on level rise. Worst-case push latency is about 7 min; no nowcast. |
| D5 | PARTIAL | UI, push text and voice in en/es/vi/zh/ar. NWS text untranslated; SMS only en/es/vi; no ASL/Braille. |
| D6 | PARTIAL | TranStar feed not obtainable. Substitute: 128 static crossings + crowd reports (0 live right now). |
| D7 | SOLVES | No legacy `waterservices` calls; OGC API used (`gauge_history.py:15`, `scripts/fetch_replay.py:9`). |

Counts: SOLVES 1, PARTIAL 9, INFORMS ONLY 3, NOT APP-SOLVABLE 1, NOT ADDRESSED 0. The cycle-35 claim of C1-C3, D1-D5 as REDUCES is generous for D2 (SMS) and C2.

## Detail

### C1 Low coverage, C2 uninsured at-risk homes
- Code: `backend/app/services/risk.py:66` (Harvey 154,170 / 36% fact, sourced to Community Impact); `services/zipinsurance.py` (OpenFEMA NfipClaims v3 / NfipPolicies v3); `frontend/src/components/RentBuy.tsx` ("Should you buy flood insurance here?"); `frontend/src/lib/summary.ts:232` (insurance action for high/elevated exposure).
- Tests:
  - `GET /zip-insurance?zip=77096` gives total 6,482 and since-2017 2,610. Direct OpenFEMA v2 gives 6,480 and 2,608 (v3 has 2 more rows). 77586: 4,792 / 522 vs v2 4,791 / 521. Match.
  - In-force policies 77096: app 4,537, OpenFEMA 4,535 on the same filter. Match.
  - UI Meyerland `#home/rentbuy` shows ZIP claims, premiums, "buying before storm season matters". Downtown (ZIP 77002, zone X) shows "Low-risk zone, but this ZIP has 74 NFIP claims since 2017".
- Gaps:
  - B1: policies in force is null for 77586, 77004, 77026, 77477 (see bug list).
  - B2: label without a ZIP gives no card (see bug list).
  - C2: `grep "92%"` in `frontend/src` has no hits. Ask answers can quote it, but no page shows it. The app gives no estimate of how many homes at this address's risk level are uninsured; it only shows ZIP claims vs policies.

### C3 30-day wait
- Code: `backend/app/services/insurance.py` (30-day add, season end Nov 30); `pages/Prepare.tsx:195` (date picker, ICS reminder at `Prepare.tsx:28`); Home action "Check when flood insurance would start".
- Tests: purchase 2026-10-11 gives effective 2026-11-10, covered_before_season_end true. 2026-11-05 gives 2026-12-05, false. 2026-11-30 gives 2026-12-30, false. 2026-12-15 gives 2027-01-14, season_end 2027-11-30, true. `garbage` returns 200 with today's date silently. UI shows "Tuesday, Nov 10", 30-day wait, exception text, ICS button.
- Numbers: 30 days matches FloodSmart. Exceptions in the countdown: mortgage made/increased/extended/renewed, and coverage change at renewal. Missing from the countdown card (present in `data/knowledge/insurance-30-day-and-gap.md`): the 1-day wait for newly designated high-risk property and after wildfire-caused flooding.
- Gaps: it is a manual calculator. It does not warn "a storm is already in the forecast, coverage will not start in time" using `/rain24` or `/outlook`. "Covered before season end" treats Nov 30 as flood season end, but Houston's worst events (Tax Day April 2016) are outside hurricane season. The app cannot shorten the wait. Verdict PARTIAL.

### C4, C6 premiums
- Code: `zipinsurance.py:_premiums` (quartiles of in-force `totalInsurancePremiumOfThePolicy`); `RentBuy.tsx` "Typical premium"; `components/p35/P35.tsx:29` PayLess.
- Tests: 77096 median $1,501 (p25 $1,007, p75 $2,188, n=4,537). 77002 median $1,828 (n=134). 77586 median $1,150 (n=4,980; OpenFEMA count 4,980). The caveat "ZIP-wide, all policy types, includes federal fees. Not a quote." is shown.
- Gap: no Risk Rating 2.0 change, no "your premium may rise X% a year", no 91% / $541 vs $1,200-$2,975 figure in the UI (Ask only). C6 (undisclosed trajectory) is not addressed; a snapshot cannot show a trajectory. The app never states that a snapshot cannot show the price trend, so it does not even flag C6.

### C5 affordability
No NFIP affordability program exists, so no app can fix it. PayLess lists three FloodSmart-sourced levers (elevation certificate, elevating, modifying) with "not an affordability program". Honest. NOT APP-SOLVABLE.

### C7 underestimation
- Code: `services/risk.py` (Harvey layer, zone, elevation), `lib/summary.ts` ("Menor riesgo no es cero: puede haber inundaciones en cualquier lugar donde llueva fuerte"), `RentBuy.tsx` lowrisk line, `/hwm`.
- Tests: Downtown zone X: `harvey.flooded=false` with note "This is not proof it stayed dry: about half of Harvey-flooded homes were outside mapped floodplains". Home summary for Seabrook says "High exposure" and for Meyerland "Flooded in Harvey". Greenville SC (Flood Advisory) correctly gives "Exposición menor ... no es cero".
- Gap: First Street 14.5M vs FEMA 9M appears only in Ask. Good address-level contrast otherwise.

### D1 gage map is not a warning system
- Code: `services/watch.py:evaluate` (NWS alerts + 3 nearest gauges + crossings within 1 km + community reports 6 h); `routers/watch.py`; `pages/Watch.tsx` (poll every 120 s); `civic.resp.1` labels the county gage map "not a notification system"; "Gauge levels are for the stream, not your street" on Home.
- Tests: `/watch/status` Meyerland/Seabrook/Downtown all "ok" (matches reality: NWS has no alerts there). With `simulate=storm`, all three become "warning" with reasons. A real Flood Watch + Flood Advisory at (35.073, -82.64) gave level "watch" with both listed.
- Gaps: only 36 gauges in `data/gauges.json` (Seabrook's nearest is 8.5 mi). Gauge age: Brays Bayou at Houston observed 11:45Z at 12:51Z (66 min) while the Home chip says "Gauges - Recent - 22 min ago" (the freshest of the three). Uses NOAA NWPS, not the Harris County FWS gages the problem names (D1 says FWS lags up to 15 min; ours lag longer).

### D2 sign-up effort
- Code: `components/AlertsSwitch.tsx` (one switch: permission, SW register, VAPID key, subscribe); `routers/push.py`; `services/push.py`; `public/sw.js` push and notificationclick handlers.
- Tests: `/push/vapid-public-key` returns an 87-char URL-safe key. `/push/test {}` gives 400 "endpoint is required"; unknown endpoint gives 404; `/push/subscribe` with a bad body gives 422. These are safe and do not broadcast. UI in headless Chrome shows "Notifications are blocked" (expected). Fallback path "Alerts show while the app is open" is honest.
- SMS: `POST /sms/simulate "ALERTS ON 77096"` replies "flood alerts ON for 77096". `grep SmsOptIn` shows the model is used only inside `services/sms.py`; there is no loop or sender that reads opt-ins. **No outbound SMS exists; the opt-in does nothing.** Same for the check-in call.
- Gaps: iOS needs 16.4+ and Home Screen (card shows a tip). HTTPS required in production. Real push delivery was not tested (not allowed to send).

### D3 alerts by county, not street or route
- Code: `services/alerts.py:get_alerts` (NWS `?point=`), `services/route.py:148` (alerts at route midpoint), `watch.py`.
- Test: for three live US flood alerts, the app's `/alerts` event list equals the direct NWS `?point=` list (match x3, e.g. Flood Advisory + Flood Watch at 35.073,-82.64, expires 09:30 -04:00). Houston places: NWS and app both empty.
- Gaps: NWS point lookup returns alerts whose polygon or zone contains the point. That is finer than county but is not road-level. Routes sample only the midpoint, so a 20 km route can cross an alert polygon the midpoint misses.

### D4 flash floods leave little time
- Code: `services/rain24.py`, `services/outlook.py` (WPC ERO), `services/push.py` (loop 300 s, first run after 30 s, push only when level rises), `services/alerts.py` (TTL 120 s, storm mode 90-180 s).
- Tests: `/rain24` Meyerland returns NWS gridpoint 6-h totals (0.00 in, max POP 2%); `/outlook` returns day 1-5 "None". Both match the dry day.
- Timing: worst case from NWS issuing a warning to a push is 120 s cache + 300 s loop = about 7 min; best case about 0 s. For "8-10 inches in 3 hours" storms that is a real lag, and the app adds no radar nowcast or rate-of-rise gauge alert beyond stage categories (`action` stage gives "watch"). Replay builds awareness (B7) but does not give lead time.

### D5 language and accessibility
- Tests:
  - UI at `?demo=1#alerts` with the storm simulated renders the full warning in en, es, vi, zh, ar (RTL for ar), with "Call 911" and "[simulated]" localized. No page errors.
  - `POST /voice` returned audio/mpeg (32-36 KB, distinct bytes) for es, vi, zh and ar.
  - Push text is defined in 5 languages (`push.py:TEXT`); es text has no accents ("Alerta de inundacion").
  - SMS: Spanish and Vietnamese replies work; zh and ar texts get the English reply (`STR` has en/es/vi only). The check-in script for zh falls back to en.
  - Real NWS alert on a Spanish UI shows "Flood Advisory" / "Flood Watch" untranslated; headline and description are English only.
- Gaps: no ASL, Braille or TTY. Language stays sticky per phone in SMS.

### D6 roadway flood feed
Feed access needs a TranStar agreement; not app-solvable. Substitute: `data/crossings.geojson` (128 static crossings) and community reports (`GET /reports` returns `[]` now). Static, not live. PARTIAL.

### D7 API decommission
No `waterservices` in `backend/app` or `scripts`; OGC API used. SOLVES.

## Ranked bug list

1. **SMS "ALERTS ON" is a no-op (D2, D5, safety).** Repro: `POST /api/sms/simulate {"from":"+15555550123","body":"ALERTS ON 77096"}` replies "flood alerts ON". `SmsOptIn` is read only in `services/sms.py`; nothing sends. A no-smartphone user is told they will be alerted. Fix: send via Twilio when configured, otherwise change the reply to "demo only".
2. **Push loop drops alerts on failed send (D4).** `services/push.py:check_all` stores `new[p["id"]] = ev["level"]` even if `_process` returned False (error). The rise is never retried. Fix: only record the level when sent.
3. **`policies_in_force` null while premiums exist (C1/C4).** Repro: `GET /api/zip-insurance?zip=77586` gives `policies_in_force:null`, `premiums.sample_size:4980`; OpenFEMA count is 4,980. Same for 77004, 77026, 77477 (`backend/.cache/zip_insurance.json`). `zip_insurance()` caches a partial result for 24 h when only premiums succeeded. Fix: fall back to `sample_size`, or do not disk-cache partials.
4. **Insurance card needs a ZIP in the place label (C1/C2/C4/C7).** Repro: seed place label "Downtown" (29.7604,-95.3698), open `#home/rentbuy`: "Search an address with a ZIP code". With "Downtown, Houston, TX 77002" it works. `RentBuy.tsx` derives ZIP by regex on the label; it should reverse-geocode the lat/lon.
5. **SMS suggests the wrong ZIP (D2).** Repro: sms "1234 Main St Houston" (resolves to 77002) replies "text ALERTS ON 77096". `services/sms.py:summarize` falls back to hardcoded `"77096"` unless the label starts with 5 digits.
6. **Storm mode is global and out-of-area watches are accepted (D1).** `POST /watch` accepts any lat/lon; `/watch/status` for Greenville SC lists Houston gauges (Luce Bayou etc.) as nearby, and the real SC Flood Advisory flipped the global `storm_mode` to true for all users (`/api/status` now shows `storm_mode: true` while Houston is dry). Fix: reject places outside the Houston area, or cap gauge distance; scope storm mode to the metro area.
7. **Wrong NWS terminology in messages (D1/D4).** A Flood Advisory (or gauge "action" stage) yields the message "Flood watch ... conditions are building" and a push titled "Flood watch" (`watch.py`, `push.py:TEXT`). NWS watch, advisory and warning mean different things. Include the real event name and expiry in the push body.
8. **Countdown copy and inputs (C3).** `covered_before_season_end` treats Nov 30 as the flood season end; a bad `purchase_date` silently becomes today; the 1-day wait for newly mapped high-risk and post-wildfire cases is missing; no check against the forecast. Fix: warn when `/rain24` or `/outlook` shows heavy rain in the next 30 days of risk, and validate the date (422).
9. **Alert content not localized (D5).** Real NWS event names, headlines and descriptions appear in English in es/ar/vi/zh UIs. SMS and the phone check-in only support en/es/vi; zh/ar fall back to English silently.
10. **Gauge freshness chip (D1).** The chip shows the freshest gauge's age (22 min) while Brays Bayou at Houston was 66 min old; threshold for "stale" is 2 h (`freshness.py:STALE_HOURS`). Show the oldest of the displayed gauges.
11. **C2/C4/C6 content only in Ask.** The 92% quote, Risk Rating 2.0 figures (91%, $541 vs $1,200-$2,975) and the 9M vs 14.5M comparison have no on-page surface.
12. **Route alert check uses the midpoint only (D3)** (`services/route.py:148`).
13. Minor: push strings in es lack accents; duplicate `/watch` POSTs create duplicate places (no dedupe); push latency about 7 min worst case with no documented SLA.
