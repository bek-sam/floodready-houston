# Cycle 5 research: honest coverage of the 52 problems (Sat Oct 10, ~8 PM)

Strict rules: REDUCES = a working feature in code/data today changes what the user can do. INFORMS = knowledge card / Ask answer / static display only. NONE = nothing exists. Code was skimmed, not run; app-plan.md is aspirational and was not trusted.

## 1. Coverage table

| # | State | What does it (file) |
|---|---|---|
| A1 | REDUCES | Route check + Watch push (routers/route.py, watch.py, Drive/Watch.tsx) |
| A2 | INFORMS | driving-in-floods.md only |
| A3 | REDUCES | Personal, timely push + route verdict instead of the slogan (Watch, Drive) |
| A4 | REDUCES | 64-crossing dataset (data/crossings.geojson) used in route check |
| A5 | REDUCES | Same crossings shown on Drive and checked per route |
| A6 | INFORMS | Crossings substitute for sensors, but nothing reports missing barricades |
| A7 | REDUCES | Push alerts and pre-trip check reach drivers before the water |
| A8 | REDUCES | Route avoidance + driving card (Drive, driving-in-floods.md) |
| A9 | INFORMS | post-flood-money-safety.md (flood cars/VIN) only |
| B1 | REDUCES | Home: FEMA zone beside Harvey inundation (services/harvey.py, harvey_inundation.geojson) |
| B2 | INFORMS | Ask / flood-zones-vs-reality.md |
| B3 | REDUCES | Home plain-language zone text plus Harvey overlay |
| B4 | INFORMS | outdated-maps-and-maptool-status.md |
| B5 | INFORMS | Same card |
| B6 | REDUCES | Mobile risk card (Home.tsx) |
| B7 | REDUCES | Replay "shift the storm" (Replay.tsx, data/replay) |
| B8 | INFORMS | Low-ground flag needs a gauge datum and is mostly empty (services/risk.py) |
| B9 | INFORMS | Renter checklist text in Prepare; nothing address-specific |
| B10 | REDUCES | Watch push + Replay of the 2026 event |
| B11 | INFORMS | Home shows the jurisdiction (risk.py `_juris`) |
| C1 | INFORMS | insurance-30-day-and-gap.md |
| C2 | INFORMS | Same card |
| C3 | REDUCES | 30-day countdown + .ics reminder (routers/insurance.py, Prepare) |
| C4 | INFORMS | risk-rating-2-premiums.md |
| C5 | INFORMS | Same card (weak, mentions the gap only) |
| C6 | INFORMS | Same card |
| C7 | REDUCES | Risk card shows real flooding vs FEMA zone |
| D1 | REDUCES | Watch merges alerts + gauges + 48h history sparklines (gauges.py, Home) |
| D2 | REDUCES | One-tap push subscribe, no validation step (push.py) |
| D3 | REDUCES | Per-place Watch and per-route check |
| D4 | REDUCES | Push + Outlook badge + Replay of rain rates |
| D5 | REDUCES | 5 UI languages, voice read-aloud, multilingual Ask |
| D6 | INFORMS | Static crossings dataset only; no live feed |
| D7 | NONE | Technical constraint, not user-facing (not verified in code) |
| E1 | REDUCES | Household profile builds a personal plan (Prepare, ai/) |
| E2 | REDUCES | Plan flags dialysis/medication early-leave; special-needs card |
| E3 | INFORMS | renters-and-buyouts.md |
| E4 | INFORMS | vulnerable-households.md; no per-address flood history |
| E5 | NONE | No closure or medical-access feature |
| F1 | INFORMS | Reservoir card + Addicks/Barker flag (Recover, reservoirs-and-dams.md) |
| F2 | INFORMS | Same flag |
| F3 | NONE | Nothing on development or paving |
| F4 | INFORMS | Bond tracker (civic.json, services/civic.py) |
| F5 | INFORMS | Same |
| F6 | INFORMS | Same |
| F7 | INFORMS | "Who's responsible" card (civic.json) |
| G1 | INFORMS | renters-and-buyouts.md |
| G2 | INFORMS | Historical 2017 shelter list, labeled historical |
| G3 | INFORMS | post-flood-safety.md |
| G4 | INFORMS | fema-aid-and-recovery.md |
| G5 | REDUCES | Community reports POST/GET stored in DB (routers/reports.py); unverified, small |
| G6 | INFORMS | Replay shows events, but no back-to-back view |

## 2. Totals (the honest pitch number)

- REDUCES: 21 of 52 (40%)
- INFORMS: 28 of 52 (54%)
- NONE: 3 of 52 (6%): D7, E5, F3
- app-plan.md claims 32 REDUCES. The honest figure is 21.
- Six F items are policy problems no app can fix, so INFORMS is the correct ceiling for them. Excluding F, REDUCES is 21 of 46 (46%).

## 3. Realistic upgrades (each 2h or less, free data)

| Problem(s) moved | Feature idea | Free data |
|---|---|---|
| B9, B2, C1, C2, C4, C6 | "Renting or buying here?" card. Given an address it shows ZIP NFIP stats (policies in force, claims, share of claims outside SFHA, average premium), the reservoir flag, Harvey inundation yes/no, and a printable 8-question landlord list. | OpenFEMA NFIP policies/claims API by ZIP (field names to verify), existing risk service |
| E4, G6, B10 | "Flood history at this address." Timeline of Harvey polygon hit, plus which replay events pushed the nearest gauge past flood stage, with the gap between events. | Existing harvey polygon, data/replay, gauge history |
| E5, E2, E1 | Medical access finder: nearest hospitals, dialysis centers and pharmacies, each with a flood-aware route check. A "your dialysis clinic is cut off" warning when a crossing blocks the route. | OSM Overpass (healthcare=*), existing OSRM route check |
| A6, A7, G5, D1 | Show community reports on the Drive map and in route-check ("2 reports within 300 m in the last 6h"). Add a "barricade missing / water over road" report type. | Existing reports table |
| G3, G4, G1, E3 | Interactive recovery tracker: checkable post-flood safety, FEMA documentation (photos, receipts, appeal deadlines) and buyout "who to call" steps, kept in localStorage. | Existing knowledge cards |
| G2 | 911 location card (address, lat/lon, nearest cross street to read aloud, one-tap copy) plus an "I'm safe" sms: link to family. No backend. | Nominatim reverse geocode |
| A9 | Add a "move your car to high ground, nearest multi-storey garage" line to Watch alerts. | OSM parking |
| B8 | Local-depression check. Sample elevation in a ring around the address and flag a bowl. This fixes the empty low-ground flag. | USGS EPQS |
| B4, B5 | Show the Atlas 14 100-yr 24h rainfall for the address versus Harvey totals. | NOAA PFDS (parsing risk) |
| F3 | Not an app fix; add a 20-minute knowledge card. | n/a |

## 4. Top 5 (problems moved x demo value)

1. **Renting or buying here?** Moves up to 6 (B9, B2, C1, C2, C4, C6), and the address demo is easy to show.
2. **Flood history at this address.** Moves E4 and G6 and strengthens B10 and C7. It has the best "it flooded here" demo moment.
3. **Medical access finder with flood-aware routes.** Turns the only functional NONE (E5) into REDUCES, makes E2 concrete, and is a strong equity story for judges.
4. **Community reports on the route.** Moves A6, makes the reports table visibly useful, and strengthens A7 and G5.
5. **Recovery tracker + 911 location card.** Moves G3, G4, G1 and G2 (4 problems) for little code; lower demo value but good counting value.

Realistic result if 1-5 land: REDUCES goes from 21 to about 35 (B9, B2, C1, C2, C4, C6, E4, G6, E5, A6, G3, G4, G1, G2 = 14; round conservatively to 33 to 35).
