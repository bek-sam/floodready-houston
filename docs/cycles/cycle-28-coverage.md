# Cycle 28 coverage recount (A9, F2, E3)

Rules as in `cycle-24-coverage.md`: REDUCES = a working feature changes what a user at an address can do. Baseline cycle 24: 33 REDUCES / 17 INFORMS / 2 NONE of 52.

| # | Was | Now | Evidence |
|---|---|---|---|
| A9 move your car | INFORMS | REDUCES | Code read: `/parking/check` (`routers/parking.py`, `services/parking.py`) and `/rain24` (`routers/rain24.py`) exist; `frontend/src/components/rain24/RainCard.tsx` and `pages/Home.tsx` reference them. The cycle 24 table missed them. UI load of Home with a test address still to confirm. |
| F2 reservoir pool vs ground | INFORMS | REDUCES, only once `GET /api/reservoir/pool` and the Civic card ship | Live NWPS ADDT2 (checked 2026-10-11: pool 83.89 ft, action 93, minor 96). Barker has no gauge, area flag only. |
| E3 tenant relocation rights | INFORMS | REDUCES, only once the RentBuy card + letter ship | Knowledge card added; sources: eCFR 49 CFR Part 24 and the Harris County buyout page (both HTTP 200 on 2026-10-11). Wording is federally-funded programs only. |

Not claimed: E5 (FAA airport line, partial, stays INFORMS), D7, D6, C5, F1, B4, B5, F3, C4.

**Total: 34 now (A9). 36 of 52 if F2 and E3 both ship; 35 if only one. Pitch "34 of 52" until the builds are verified in the UI.**

Hygiene: `grep waterservices scripts/` returned no hits.
