# Cycle 39 plan (freeze 11:00, builders done by ~10:15)

Input: docs/problems verify-AB/CD/EFG (28 PARTIAL). Score = harm x frequency x demo / effort. All picks use free data or text already in the repo. Do not touch ports 8000/5173.

Dropped after checking code: F7 council name (already rendered in `WhoToContact.tsx`, role `council`, so the audit gap is stale); G2 SMS 911 line (already fixed in `sms.py`).

## 1. Detour when route is "avoid"/"caution" (A1, A7, A8) - backend + frontend
- Verified live: `router.project-osrm.org/route/v1/driving/...?alternatives=true` returns 2 routes (11.9 km vs 9.0 km test).
- Backend (`backend/app/services/route.py`): request `alternatives=true`. Factor the crossing/report scan (`_min_dist_m` against BUFFER_M and REPORT_BUFFER_M) into a helper. If verdict is avoid or caution and hazards exist, scan routes[1:]. Keep the alternative with the fewest hazards, only if it has strictly fewer hazards than the primary. Cache key unchanged (the diskcache entry stores the whole response).
- Response (additive, optional): `alternative:{route:LineString, hazards:[...same shape], hazard_count:int, extra_min:float, extra_mi:float, message_code:"route.alt", message:"A route with fewer known flood-prone spots adds ~N min."}`. Absent when none is better. The primary verdict is unchanged. No wording that says the alternative is "safe".
- Frontend (`pages/Drive.tsx`): draw the alternative as a dashed polyline and show a card with the extra minutes and the hazard count. Add i18n key `route.alt` in 5 languages.
- Accept: `POST /route-check` for a demo route with `?simulate=storm` returns `alternative` with `hazard_count` < primary or omits the field. Unit test with a mocked OSRM payload. Drive page at 390 px shows the card. OSRM down means no `alternative` and no crash.
- Moves: A8 PARTIAL to SOLVES-leaning. A1 and A7 gain a concrete action, still PARTIAL.

## 2. Dialysis center flood exposure (E2) - backend + frontend
- Backend (`services/medical.py`): for the nearest `limit` facilities (max 5), concurrently call the existing FEMA lookup (`risk._fema`) and `harvey_at`. Add `fema_zone`, `sfha`, `harvey_flooded` (true/false/null) to each facility. Wrap in try/except and set null on failure. Add `exposure_source` URLs (the FEMA NFHL URL already in the repo). Keep the cap at 5 so latency stays low.
- Frontend (`MedicalAccess.tsx`): show a badge "In high-risk flood zone (AE)" or "Flooded in Harvey" with "Call to confirm they are open". Localize the `note` in es/ar/vi/zh (audit gap 1).
- Accept: `GET /medical?lat=29.678&lon=-95.464` returns the new fields on each item. A test with mocked FEMA covers the failure path (fields null, 200 OK). Both badge and note render in es.
- Moves: E2 stays PARTIAL, but it removes the live.py "flood exposure" overclaim.

## 3. Recover: buyout hotline + "waiting for rescue" card (G1, G2) - frontend only (~30 min)
- G1: in `pages/Recover.tsx` buyout list, step b2 (or a new b0) gets a `tel:+13462864020` button (HCFCD buyout hotline, text already in `P35.tsx:BuyoutContact`; reuse that constant and source).
- G2: new `WaitingForRescue` card next to `Share911` in `RecoverExtras.tsx`. It uses the same attic/roof wording already shipped in `backend/app/services/sms.py` `danger` (highest level, no closed attic, roof only if necessary, signal from a window, keep the phone charged, text 911 if calls fail) plus the `tel:911` button and the Share-911-location button. Use the same source URL as the sms.py copy. Add i18n in 5 languages.
- Accept: the Recover page buyout list contains "4020" in the DOM. The card is visible in en and es. The build and the i18n check show 0 missing.
- Moves: G1 and G2 gaps closed in-app. Verdict stays PARTIAL (the app cannot speed rescue or buyouts).

## Assignments (one builder per folder)
- backend/ (excl. app/ai): picks 1 then 2 (route first, about 45 min each)
- frontend/: pick 3 first, then the UI parts of 1 and 2
- data/ + scripts/, backend/app/ai: none
Unused ideas: council name UI (stale), the C3 forecast-aware 30-day warning (needs rain24 plumbing, over 1 h).
