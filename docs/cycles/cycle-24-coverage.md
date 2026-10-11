# Cycle 24: strict coverage recount (Sun Oct 11, before the 1 PM demo)

Rules (same as cycles 5, 12, 13): REDUCES = a working feature in the current code changes what a user at an address can do about that problem. INFORMS = a knowledge card, a static display or an advocacy message only. NONE = nothing user-facing. Problem wording is from `flood-problems.md` (52 problems). Baseline: cycle 13 = 33 / 17 / 2 (`docs/cycles/cycle-12-research.md`, `cycle-13-research.md`, `CHANGELOG.md`). Code checked: `frontend/src/pages`, `frontend/src/components`, `backend/app/routers`, `backend/app/services`.

## Result

**33 REDUCES / 17 INFORMS / 2 NONE of 52 (63%). No change from cycle 13.**
The cycle 14-23 features mostly deepen problems that were already REDUCES. None of the 19 remaining problems passes the strict test (see section 2). The pitch number stays **33 of 52**.

## 1. Full table

| # | State | What acts on it now (cycle 24 code) |
|---|---|---|
| A1 | REDUCES | Route check (`routers/route.py`), Watch push, SMS ALERTS ON (`routers/sms.py`) |
| A2 | INFORMS | Driving card only |
| A3 | REDUCES | Personal route verdict and push instead of the slogan; underpass warning poster with QR to `#drive/to=lat,lon` (`components/poster`) |
| A4 | REDUCES | 128 crossings (was 64): +54 USGS STN high-water marks at crossings, +8 re-geocoded KPRC, +2 OSM underpasses (`data/crossings.geojson`, `scripts/build_crossings.py`) |
| A5 | REDUCES | Same 128 crossings on Drive map and in the route check; "No known flood-prone crossings" wording instead of "safe" |
| A6 | REDUCES | Report kinds `barricade_missing`, `water_over_road` count as route hazards within 100 m / 24 h (since cycle 12) |
| A7 | REDUCES | Push, SMS and pre-trip check; poster at the underpass itself |
| A8 | REDUCES | Route avoidance and driving card |
| A9 | INFORMS | Flood-car/VIN money-safety card only. No "move your car" feature exists (grep found none) |
| B1 | REDUCES | Home shows FEMA zone beside Harvey flooded/not. Now citywide: 357,241 City of Houston Harvey polygons in SQLite R*Tree; outside coverage returns null ("no Harvey extent data"), never a false "not flooded"; 2,093 USGS high-water marks (`routers/hwm.py`) |
| B2 | REDUCES | RentBuy low-risk-zone line plus ZIP NFIP claims (cycle 13) |
| B3 | REDUCES | Plain-language zone text beside observed flooding; Compare places (`pages/Compare.tsx`) |
| B4 | INFORMS | Outdated-maps card only |
| B5 | INFORMS | Same card |
| B6 | REDUCES | Mobile risk card, 390 px layout, easy-read mode (`components/easyread`) |
| B7 | REDUCES | Replay "shift the storm", 3D replay (`components/replay3d`) |
| B8 | INFORMS | Borderline, not counted: citywide Harvey layer and 311 drain link (`components/civic311`) exist, but `services/harvey.py` itself states street/drainage flooding is not in that map |
| B9 | REDUCES | Tenant flood-disclosure letter generator and renting/buying card (cycles 11-12) |
| B10 | REDUCES | Watch push, SMS, Replay of the June 2026 event |
| B11 | REDUCES | Jurisdiction, floodplain administrator, commissioner, council member with phone (`components/WhoToContact.tsx`); 311 card by jurisdiction |
| C1 | REDUCES | Insurance decision block: zone + ZIP claims + premium range + 30-day wait |
| C2 | REDUCES | Same block, with a next step |
| C3 | REDUCES | 30-day countdown and .ics reminder; storm-season .ics reminders (`components/season`) |
| C4 | INFORMS | Snapshot premium range only, no trend |
| C5 | INFORMS | No affordability program exists or is linked |
| C6 | INFORMS | Borderline, not counted: ZIP-wide premium range is a distribution, not a quote or a trajectory |
| C7 | REDUCES | Observed flooding next to the FEMA zone; HWM depths; Compare places |
| D1 | REDUCES | Watch merges alerts and gauges; 48 h sparklines; data freshness `meta{as_of,source,freshness}`, gauge flags stale/provisional/offline, `#status` page of 12 sources (`routers/status.py`) |
| D2 | REDUCES | One-tap push; SMS needs no account validation |
| D3 | REDUCES | Per-place Watch, per-route check, rounded-coordinate buddy alerts |
| D4 | REDUCES | Push, rain-outlook badge, coastal tide anomaly and active Gulf storms (`routers/coastal.py`), evacuation zone and NHC surge (`routers/evac.py`, Seabrook Zone A) |
| D5 | REDUCES | 1,338 strings x 5 languages, 0 missing (`scripts/i18n_coverage.mjs`); backend warnings carry codes rendered in 5 languages; voice in 5 languages; SMS HELP/AYUDA; easy-read mode |
| D6 | INFORMS | Static crossings and community reports; the live TranStar feed is still not public |
| D7 | NONE | Not user-facing. `#status` shows source health, which would expose a retired API, but that is monitoring, not a fix |
| E1 | REDUCES | Household plan; neighbor check-in buddy system (up to 5 people, call/SMS links, marked-safe); pets tab; go-bag; easy-read |
| E2 | REDUCES | Dialysis/medication early-leave flag; 117-facility dialysis finder with tel: links; special-needs card |
| E3 | INFORMS | Tenant letter covers flood notice and lease rights, not buyout displacement |
| E4 | REDUCES | Per-address flood history card (since cycle 8) |
| E5 | INFORMS | Dialysis finder says "confirm storm closures by phone"; no closure feed |
| F1 | INFORMS | Reservoir/dam explainer and Addicks/Barker flag |
| F2 | INFORMS | Same flag |
| F3 | NONE | Nothing on development or paving |
| F4 | INFORMS | Bond tracker, copyable message (advocacy) |
| F5 | INFORMS | Same |
| F6 | INFORMS | Same |
| F7 | REDUCES | Named officials with tel/mailto and copyable message |
| G1 | INFORMS | Borderline, not counted: buyout proximity is approximate, 311 phones are generic, no buyout-program contact or timeline |
| G2 | REDUCES | 911 location card; evacuation zone and surge for coastal addresses; SMS HELP |
| G3 | REDUCES | Post-flood hazard guidance in Recover |
| G4 | REDUCES | FEMA aid steps and recovery tracker; flood-damage photo helper (IndexedDB, room-by-room, HTML report export, never uploaded). Photos help documentation, so G4 was already counted and is not double-credited |
| G5 | REDUCES | Community reports stored and used by the route check (unverified, small) |
| G6 | REDUCES | Flood history by address (Harvey, Tax Day, Imelda, June 2026 peaks) |

Totals by group: A 7 of 9, B 8 of 11, C 4 of 7, D 5 of 7, E 3 of 5, F 1 of 7, G 5 of 6.

## 2. New candidates checked and why the total did not move

| Candidate (since cycle 13) | Problem it touches | Decision |
|---|---|---|
| Evacuation zones and surge (`/api/evac`) | D4, G2 | Already REDUCES. Deepened for coastal addresses (Seabrook Zone A, Cat 2-5 surge). No new problem |
| High-water marks (`/api/hwm`, 2,093 marks) | B1, C7, A4 | Already REDUCES. HWM also feed 54 crossings |
| Coastal tide and storms | D4 | Already REDUCES |
| Go-bag, pets, season .ics | E1, C3 | Already REDUCES |
| Posters | A3, A7 | Already REDUCES |
| 311 card | B11, F7, B8, G1 | B11, F7 already REDUCES. B8 and G1 stay INFORMS (borderline) |
| Photo documentation | G4 | Already REDUCES |
| Buddy check-in | E1, D3 | Already REDUCES; E2 unchanged |
| Compare places | B3, C7 | Already REDUCES |
| Easy-read, full localization, SMS | D5, E1 | Already REDUCES. Strengthens the claim, adds no problem |
| Data freshness and `#status` | D1, D3 | Already REDUCES. D7 stays NONE (monitoring, not user-facing) |
| Citywide Harvey (357,241 polygons) | B1 | Already REDUCES. Honest null outside City of Houston |
| 128 crossings | A4, A5 | Already REDUCES |

Downgrades considered: none. Every REDUCES row above points to a file or endpoint that exists in the repo today.

## 3. Pitch wording

"Directly reduces 33 of 52 documented Houston flood problems (63%). The other 19 are mostly policy problems (dams, flood bond, development, insurance affordability) that we make visible and actionable." Say "33", not 27 or 32.
