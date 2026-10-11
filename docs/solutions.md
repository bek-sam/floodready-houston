# Extra implementable solutions by problem group (ranked impact/effort, solo ~18h; beyond app-plan.md)
Rank = (impact high->low). Effort in hours.

## A. Driving into water
1. Auto-"avoid list" overlay: render all HCFCD bond/detention + TranStar sensors + KPRC crossings on one layer; red when linked gauge >= action stage (1.5h).
2. Share/SMS-style card "Don't take Main St underpass tonight" with deep link (0.5h).
3. Nearby high-ground / "safe stop" suggestions from EPQS elevation grid around the route (1.5h).
4. Rainfall-last-1h badge on crossings via Open-Meteo (1h).
5. Pre-trip browser Notification when a Flash Flood Warning hits home/work polygons (1.5h).

## B. False sense of safety (maps)
1. "Was your address under Harvey?" point-in-polygon on pre-simplified Houston Harvey Inundation layer (2h, high wow factor).
2. Side-by-side card: FEMA zone vs Harvey extent vs elevation (1h).
3. Atlas 14 rainfall slider toy: inches of rain -> nearby gauges' historical stage response (2h).
4. Accessible color + text-first risk card for phones (1h).

## C. Insurance / money
1. Insurance countdown add-to-calendar .ics download (0.5h).
2. "Do I need flood insurance?" 5-question checklist keyed on FEMA zone and renter status, linking FloodSmart (1h).
3. Document-your-stuff photo checklist stored locally (1h).

## D. Warnings / alerts
1. Multilingual pre-generated audio for each NWS alert type (5 langs x ~6 types, cached MP3s) (1h).
2. Web Push / email digest signup (no account) (2h).
3. Alert timeline from NWS `alerts?area=TX&event=...` for Harris County zone (0.5h).
4. Printable/offline "go-bag + evacuation" PWA page with service worker cache (1.5h).

## E. Vulnerable households
1. Profile-driven checklist (dialysis, oxygen, pets) printable + TTS (1h).
2. 2-1-1 Texas / 311 / shelter link-outs by language (0.5h).
3. "Check on a neighbor" share link with pre-written text (0.5h).

## F. Accountability / civic
1. "Bond projects near me" from `Bond_CIP_Structural_CJO` (budgeted vs spent, status, hyperlink) - 2h, best accountability feature, real data.
2. Watershed/precinct lookup with who-to-call table (1h).
3. Reservoir pool polygon check from Fort Bend Barker layers (1.5h) + disclosure line.
4. Jurisdiction (city/county/unincorporated) via `City_Limit_Boundaries_FL` (1h).

## G. Recovery / safety
1. Post-flood checklist with photos/timestamps saved locally for FEMA claims (1.5h).
2. Community reports map with moderation-lite (rate limit + flag) in Tiger hypertable (2h).
3. Buyout eligibility decision tree (1h).
4. Solana memo hash of reports (0.75h, stretch).
