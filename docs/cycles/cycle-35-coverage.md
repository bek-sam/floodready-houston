# Cycle 35 coverage recount (after cycles 29-34)

Rules as in `cycle-24-coverage.md`: REDUCES = a working feature changes what a user at an address can do. Baseline `cycle-28-coverage.md`: 36 REDUCES / 14 INFORMS / 2 NONE of 52 (counting F2 and E3 as shipped).
Cycles 29-34 (CHANGELOG.md:177-203) are audit, language, accessibility, trace, recovery and demo-storm work. They deepen problems already REDUCES. No problem moves.

## 1. Recount of the 16 non-REDUCES problems

| # | State | Cycle 29-34 candidate | Code evidence | Decision |
|---|---|---|---|---|
| A2 | INFORMS | none | - | stays |
| B4 | INFORMS | none | outdated-maps card only | stays |
| B5 | INFORMS | none | same card | stays |
| B8 | INFORMS | Rain already fallen 24/72 h (cycle 32); NWS warning polygons | `services/rain24.py`, `routers/rain24.py:8`, `components/rain24/RainCard.tsx:62` (links to Harris County FWS gauges) | Stays. Open-Meteo model estimate, not a gauge. It does not show whether drains or ditches at the address flood. `services/harvey.py` still says street flooding is not covered |
| C4 | INFORMS | none | snapshot premium range only | stays |
| C5 | INFORMS | SBA loans card (cycle 33) | `pages/Recover.tsx` | Stays. SBA is post-disaster loans, only when a declaration exists. It is not insurance affordability |
| C6 | INFORMS | none | - | stays |
| D6 | INFORMS | "Still there / Cleared" votes on reports (cycle 32) | `routers/reports.py:48` (`/reports/{id}/vote`), `components/VoteButtons.tsx`, `pages/Drive.tsx:208` | Stays. Crowd reports (6 h window) already counted under G5/A6. This is not the TranStar feed the problem names, and it is small and unverified |
| D7 | NONE | none | `#status` is monitoring | stays |
| E5 | INFORMS | `/airports/status` (cycle 28) | `routers/airports.py:8` exists. grep of `frontend/src` finds no use | Stays. Backend only, no UI |
| F1 | INFORMS | none | Reservoir explainer only. The pool gauge (`routers/reservoir.py:8`) was credited to F2 | stays |
| F3 | NONE | none | - | stays |
| F4, F5, F6 | INFORMS | none | bond tracker and advocacy message | stays |
| G1 | INFORMS | none | grep for the buyout hotline number, a survey link and "4020" in `frontend/src`, `data/knowledge`, `backend/app` returned no hits | stays |

Cycle 33 (declarations banner, proof-of-loss calculator, SBA, mold) strengthens G3/G4. Both are already REDUCES, so there is no double credit.

**Recount: 36 REDUCES / 14 INFORMS / 2 NONE of 52 (69%). No change. Pitch "36 of 52" only once the cycle 28 F2 and E3 builds are verified in the UI. Otherwise say 34.**

## 2. Three cheapest conversions (each at most 1 h, no key)

All URLs below were fetched on 2026-10-11.

1. **G1 buyouts, "who do I call"** (INFORMS to REDUCES). The app has `GET /buyout-area` (`routers/buyouts.py:10`) but no program contact. Add to the buyout card:
   - A `tel:` link to the Home Buyout Hotline, 346-286-4020.
   - A link to the "Volunteer for a Home Buyout" Survey123 form.
   - A line that the page states no timeline and that the program is not immediate recovery help.
   - Source: https://www.hcfcd.org/Buyouts (HTTP 200). The page names the "Home Buyout Hotline at 346-286-4020" for eligibility, application status, process and relocation, plus the general line 346-286-4000. Form: https://survey123.arcgis.com/share/dced0658099e45c5a2059748577d4beb
   - Do not state an approval time. The KSAT "18 months" figure is in `flood-problems.md` and is not on the HCFCD page.

2. **C4 / C6 premium levers** (INFORMS to REDUCES for C4 only if the card is address-aware, otherwise stays). Add a "Ways to pay less" block to the insurance decision card, using only what FloodSmart states:
   - Elevation certificates "aren't required... but they can help you pay less."
   - "Elevating your home is one of many ways you can get a flood insurance discount."
   - You can modify your home to "pay less for flood insurance."
   - Source: https://www.floodsmart.gov/flood-insurance-cost (HTTP 200). The page does not mention installment payments, deductibles or CRS, so do not claim them. Fema.gov pages returned 403 to curl, so verify any FEMA URL in a browser before citing it.
   - This is a lever, not an affordability program. Keep C5 INFORMS.

3. **E5 critical services: show airport ground stops** (weak conversion). `/airports/status` already exists. Show a one-line IAH/HOU status chip on Home or Drive from FAA NAS. The XML feed responded live: `https://nasstatus.faa.gov/api/airport-status-information` (`Update_Time` Sun Oct 11 12:24 GMT). The human page https://nasstatus.faa.gov/ returns 200. This lets a traveller decide whether to head to the airport, which covers only the IAH part of E5. Hospitals, METRO and food banks stay uncovered. The chip must carry the FAA source and "not official guidance".

Not recommended: B4/B5 deep link to the MAAPnext map. https://www.maapnext.org/Interactive-Map loads (HTTP 200) but I could not confirm an address search or the draft-map disclaimers on it. Verify in a browser first. The disclaimer text on https://www.hcfcd.org/MAAPnext is verified: draft maps are "informational and educational purposes only", "not open for public comment at this time".

## 3. Structural, no app can reduce
- F1 dam condition and F3 development: owner and permitting decisions. F4, F5, F6 bond delivery, partner funding and prioritisation are governance. The app can only make them visible and give the contact.
- C5 affordability: no NFIP affordability program exists. Only Congress or FEMA can create one.
- D6: the live TranStar roadway feed needs an access agreement.
- D7: an internal build risk, not a user-facing problem.
- B5: map timing is FEMA's.

## After the cycle 35 build
G1 shipped (HCFCD Home Buyout Hotline 346-286-4020 + volunteer form in Renting/buying, `frontend/src/components/p35/P35.tsx` BuyoutContact, verified in the browser) → REDUCES. C4 ("Ways to pay less") is generic, not address-aware → stays INFORMS. E5 airport chip covers airports only → stays INFORMS.

Recount: 37 REDUCES / 13 INFORMS / 2 NONE of 52
