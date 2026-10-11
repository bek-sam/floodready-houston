# Cycle 8 research (Sat Oct 10, ~9:50 PM)
Endpoint values below were verified against the running :8000 server.

## 1. Demo-critical endpoints and `scripts/demo_check.py` spec
Plain `urllib`/`httpx`, base `http://localhost:8000/api` (arg `--base` overrides it for the Vultr URL). Each step prints `PASS|FAIL name detail`. Exit code is 1 if any step fails. Timeout is 30 s per call. Run it before each demo and after every deploy.

| # | Call | Assert |
|---|---|---|
| 1 | GET /health | status=="ok" and keys has gemini, elevenlabs, backboard, db (booleans) |
| 2 | GET /risk?lat=29.6847&lon=-95.4698 (Meyerland) | harvey.flooded is True, fema_zone=="AE", elevation_ft is not None, harvey.source starts with https |
| 3 | GET /flood-history same point | harvey.flooded True, events has ids taxday-2016 and harvey-2017, harvey nearest_gauge.peak_category=="major" |
| 4 | GET /route-check/demo?simulate=storm | len>=1, and the label contains "Allen" |
| 5 | POST /route-check?simulate=storm, body = origin 29.7648,-95.3665 and destination 29.7648,-95.356 (Allen Pkwy) | verdict=="avoid", len(hazards)>=1, route.coordinates is non-empty |
| 6 | The same POST without simulate | verdict in safe/caution/avoid (a soft check; log it) |
| 7 | POST /ask {question:"My street is flooding, what do I do?", lang:"es"} | "911" in answer, sources is a list. Retry once, since a cold index is slow. |
| 8 | POST /ask {question:"Did my neighborhood flood before?", lang:"en", lat:29.6847, lon:-95.4698} | "Harvey" in answer |
| 9 | GET /shelters?lat=29.68&lon=-95.46 | any_open is False, historical is True, len(shelters)>=1, "311" in note |
| 10 | GET /zip-insurance?zip=77096 | claims.total>=6000 (currently 6482), claims.since_2017>0, claims.by_year is non-empty |
| 11 | GET /crossings | FeatureCollection, features>=1, properties has id, name, risk in high/medium, and sources non-empty |
| 12 | GET /replay/events, then /replay/{first id} | gauges is non-empty, series is non-empty, flood_stages has action/minor/moderate/major |
| 13 | GET /insurance/countdown?purchase_date=2026-10-10 | days_wait==30 and source is set |
| 14 | GET /alerts?lat&lon | has the alerts key (a list may be empty) |
| 15 | GET /medical?lat=29.68&lon=-95.46 | the result is non-empty (check the keys at runtime) |
| 16 | GET /watch/status?ids=<id from POST /watch>&simulate=storm | level in watch/warning (not ok) |
| 17 | POST /plan with a minimal profile | steps is non-empty, generated_by in gemini/template |
| 18 | GET / on :5173 or the deployed URL | HTTP 200 (flag `--front`) |

Also check:
- POST /ask with 600 chars returns 422.
- POST /route-check without simulate does not 500.
- /push/vapid-public-key returns a key.

## 2. Mobile 375px review (from code)
1. **App.tsx:114 bottom nav, `grid-cols-7` with `text-[10px]`.** Each cell is about 53 px. Labels like "Preguntar", "Recuperar" and Vietnamese "Chuẩn bị" or "Phục hồi" will clip or overflow. Fix: add `overflow-hidden`, `truncate` and `w-full` to the label span, and use `text-[10px] leading-tight`. Better: make it `grid-cols-4`, keep the 4 core tabs (Home, Drive, Prepare, Ask) and put Replay, Recover and Watch under a "More" button. Small fix at about 10 min: `min-w-0` on each button plus the label `truncate`.
2. **App.tsx:122 fixed bar.** Add `pb-[env(safe-area-inset-bottom)]` so it clears the iPhone home indicator. The `pb-28` on main is fine.
3. **App.tsx:92 header.** The lang select, install button and theme button sit on one row with the title. At 375 px it wraps, because `flex-wrap` is already set. This is acceptable, but the select needs `max-w-[9rem]`.
4. **Long-word overflow.** There is no `break-words` or `overflow-wrap` anywhere (grep returned nothing). Fix in index.css: `body { overflow-wrap: anywhere; }` (or `break-words` on cards). Do this together with the lang attribute below. Vietnamese is mostly short syllables, so the real risk is long URLs, addresses and Spanish compounds such as "Recuperación".
5. **StageChart.tsx:64 table.** It is already wrapped in `overflow-auto` with `max-h-64`, so it is OK. **RentBuy.tsx:35** is a 2-column table of years and is OK, but the by-year list can be long: wrap it in `max-h-48 overflow-auto`.
6. **maps.tsx:12 default `h-72 sm:h-96`.** All five callers set a height (Drive `h-96` at 384 px is tall at 667 px viewport height; change it to `h-72 sm:h-96`). Replay uses `h-80`. All are bounded, so there is no zero-height bug.
7. **Prepare.tsx:74 `min-w-40 flex-1`** is fine. No fixed pixel widths exist anywhere in src, and `body` has `overflow-x:hidden`.
8. **Set `<html lang>`** on language change if it is not set already: it affects hyphenation and screen readers.

Verify by resizing Chrome to 375x667 and tapping through all 7 tabs in es and vi.

## 3. Remaining weak flood problems (cycle-6 totals: 2 NONE, 25 INFORMS)
- **D7 and F3 (NONE).** These are policy items, so they cannot be built in code. Reword them honestly in the pitch.
- **A6 (INFORMS to REDUCES), about 45 min.** Cycle 6 added barricade and water-over-road report kinds. Surface them as `hazards` in /watch/status as well, so a Watch place goes to level "watch" when a fresh report is within 100 m. This makes the Watch feature actionable.
- **E4 and G6, flood history (now built).** Re-score them as REDUCES in docs/devpost.md and app-plan.md, because /flood-history exists since cycle 6. This takes 10 min and raises the headline number (25 to 27 or 28).
- **B2, C1, C2, C4, C6 (INFORMS), about 1 h.** ZIP claims data triggers no action. Add one rule to Prepare: if the ZIP has since_2017 claims >= 500 and the user is a renter, put "Ask landlord about flood history" and the flood-insurance steps first in the generated plan. This moves two to three items to REDUCES.

## Top 5 ranked
1. Write `scripts/demo_check.py` (30 min) and run it on the deployed URL.
2. Fix the bottom nav so labels do not clip (item 2.1, 10 to 20 min), then test es and vi at 375 px.
3. Re-score E4 and G6 to REDUCES and update the devpost number (10 min).
4. Add `overflow-wrap:anywhere`, `env(safe-area-inset-bottom)` and Drive map `h-72 sm:h-96` (10 min).
5. Feed fresh community reports into /watch/status (45 min), or the ZIP-claims renter rule in Prepare (about 1 h).
