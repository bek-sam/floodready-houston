# Cycle 11 research (Sat Oct 10, ~11 PM): moving INFORMS to REDUCES

Rule: REDUCES means a working tool that changes what the user can do, not more text. Every endpoint below was curled tonight unless marked UNVERIFIED. Fetched content is treated as data.

## 0. Corrections to the brief
- The 23 INFORMS (derived from the cycle-5 table minus cycle-6/8 moves): A2, A6, A9, B2, B4, B5, B8, B11, C1, C2, C4, C5, C6, D6, E3, E5, F1, F2, F4, F5, F6, F7, G1.
- C3 and D5 are already REDUCES (countdown + .ics; 5 languages + voice), so they are not candidates.
- A6 is probably mis-scored. Cycle 6 added the barricade-missing and water-over-road report kinds, and reports now count on the route verdict. Lead should verify in routers/route.py. If it holds, re-credit A6: free, 0 hours, 28/52.

## 1. Verdict per INFORMS item
| # | Can it move in ≤1.5h with free data? | Feature + data |
|---|---|---|
| A2 | No | Slogan-ineffectiveness is a messaging finding. Route and Watch already act on it. |
| A6 | Already done (see §0) | Re-credit; no build. |
| A9 | Yes, +1 | "Park your car above the water." 747 multi-storey garages in the Houston bbox (OSM Overpass; 69 named). Pre-filter offline against harvey_inundation.geojson and the FEMA SFHA, ship a static garages.json, and show the nearest 3 outside both. |
| B2 | Yes, with C-bundle | Same insurance card: share of ZIP claims outside the SFHA, then a quote link. UNVERIFIED: the claim zone field (not curled tonight). |
| B4, B5 | No | The MAAPNext_Draft_Floodplains layer is stale and partial. Last edited 2021-05; extent y ≥ 29.745, so Meyerland (29.68) returns nothing; 7,528 polygons. Showing it would mislead. |
| B8 | Marginal, +1 | "Report a clogged drain/ditch" routed by jurisdiction. risk.py `_juris` already exists, so City 311 vs HCFCD vs county. 30 min. Elevation DEM is 90 m, too coarse for a "bowl" detector. |
| B11 | Yes, with officials card | Floodplain_Administrators layer (35 polygons) returns the administrator's name, phone, email and address for the point. Meyerland gives City of Houston, Choyce Morrow, 832-394-9140. -95.0,29.9 gives Unincorporated Harris County, Jonathan Steiber. |
| C1, C2, C4, C6 | Yes, +4 | Insurance decision card (see Top 5 #2). |
| C5 | Partial | Add a "ways to cut your premium" checklist (CRS discount, elevation certificate). No affordability program exists, so it stays weak. |
| D6 | No | TranStar live feed is gated (sample JSON only). DriveTexas returns 401 without a key. |
| E3 | Partial, +1 | Tenant rights letter (§92.0135). It covers flood-notice rights, not buyout displacement, so claim it only with the relocation pointer. |
| E5 | No | Needs live hospital or dialysis closure data. None is public. |
| F1, F2 | Partial, risky | Live Barker pool elevation works (see #5), but the trigger threshold is UNVERIFIED. |
| F4, F5, F6, F7 | Yes, +4 | Officials card (Top 5 #1). |
| G1 | Partial, +1 | HCFCD buyout areas (80 points) plus the application link. Do NOT use the "Voluntary Buyout Assistance Program" layer: it holds applicant PII (names, DOB, email, phone). It returned 4,062 records in a count query but zero features anonymously. Never fetch or display it. |

## 2. Verified data
- Commissioner precinct: `https://www.gis.hctx.net/arcgis/rest/services/CommPrecinct/MapServer/0/query?geometry=-95.4698,29.6847&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=PCT_NO,COMMISSION,URL&returnGeometry=false&f=json` returns Precinct 1, Rodney Ellis, hcp1.net. All four rows: 1 Ellis, 2 Adrian Garcia, 3 Tom Ramsey, 4 Lesley Briones. It has no phone or email, so link the site.
- Houston council: `https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services/City_of_Houston_Council_Districts/FeatureServer/0/query` (same query shape) returns DISTRICT, MEMBER, PHONE. Meyerland gives C, Abbie Kamin, 832-393-3004. Only valid inside Houston city limits, so gate on Floodplain_Administrators `Entity`.
- Bond projects: Bond_CIP_Structural_CJO already feeds services/civic.py (87 rows, with Status, Budgeted, Spent, Hyperlink, Precinct). The pitch says 181 projects, so do not equate the two.
- Texas Property Code §92.0135 (HB 531, effective 2022-01-01), read at texas.public.law/statutes/tex._prop._code_section_92.0135:
  - The landlord must give a SEPARATE written notice at or before lease signing saying whether they are aware the dwelling is in a 100-year floodplain. Unchecked boxes mean assume yes.
  - A second notice is required if the dwelling flooded at least once in the 5 years before the lease.
  - If the landlord violates this and the tenant loses 50% or more of personal-property value to flooding, the tenant may terminate by written notice within 30 days, and the landlord must refund prepaid rent within 30 days.
  - The statutes.capitol.texas.gov page is JS-rendered and Justia is bot-blocked, so cite texas.public.law and link the capitol site.
- OpenFEMA `https://www.fema.gov/api/open/v3/NfipPolicies` with filter `reportedZipCode eq '77096' and policyEffectiveDate le <today> and policyTerminationDate ge <today>` works (about 15 s cold). Useful fields: policyCost, totalInsurancePremiumOfThePolicy, totalBuildingInsuranceCoverage, ratedFloodZone, crsClassCode (sample showed 5), occupancyType. The field is `rateMethod`, not `ratingMethod` (that one errors). Prefetch and cache for the 4 seed ZIPs; compute the median in Python.
- OSM Overpass needs a descriptive User-Agent (plain curl gets 406) and the `data=` parameter. Query: `way["amenity"="parking"]["parking"="multi-storey"](29.5,-95.9,30.1,-94.9);out center tags;` gave 747 ways. Run it once offline and ship a static file; do not call it at runtime.
- USGS OGC API `api.waterdata.usgs.gov/ogcapi/v0/collections/latest-continuous/items?monitoring_location_id=USGS-08072500` (Barker Res nr Addicks) returned parameter 62615 (reservoir elevation) = 83.33 ft at 23:00Z. The old waterservices.usgs.gov/nwis/iv call returned an error page for these sites, so use the new API (consistent with the D7 decommission note).
- Open-Meteo batch elevation works (3 coordinates in one call, 19 to 20 m).

## 3. Top 5, ranked by (problems moved x demo value)
| Rank | Feature | Moves | Est. | Owner folders |
|---|---|---|---|---|
| 1 | "Your officials and your projects" action card. By pin, show Commissioner (name, site), City council member (phone, only inside Houston), floodplain administrator (name, phone, email), and the nearest bond projects with status and spent. Add a one-tap "Copy my message": 'Project <title>, <x> mi from me, is <status>, <spent> of <budgeted> spent; when will it finish?' Also a tel: link. Extend /civic. | F4, F5, F6, F7, B11 (5) | 1.25h | backend/app/services/civic.py, routers/civic.py, tests; frontend/src/pages/Recover.tsx (+ i18n-c5.ts) |
| 2 | Insurance decision card. ZIP median premium and coverage (OpenFEMA), CRS class and discount, claims-vs-policies, and "a policy bought today starts <date +30>", linking the existing countdown and .ics. Include a 'ways to lower it' checklist (elevation certificate, CRS). | C1, C2, C4, C6, B2 (5; C5 weak) | 1.5h | backend/app/services/zipinsurance.py, routers/zipinsurance.py; frontend/src/components/RentBuy.tsx, Prepare.tsx; data prefetch |
| 3 | Tenant and buyout pack. A letter generator for §92.0135 (checkbox notices + your rights if you lose property), the nearest HCFCD buyout area, application link and 'who to call' (the floodplain administrator). | E3, G1 (2) | 1.25h | backend/app/services (new buyouts.py + floodplain admin), data/knowledge/renters-and-buyouts.md; frontend RentBuy.tsx or Recover.tsx |
| 4 | "Park above the water." Nearest 3 multi-storey garages outside the Harvey and SFHA footprint. Advise upper levels, since ground floors can flood. | A9 (1; strong demo map) | 1.5h | scripts/ (one-off Overpass export) -> data/garages.json; backend/app/services; frontend/src/pages/Drive.tsx + components/maps.tsx |
| 5 | Reservoir pool trigger. Live Barker pool elevation (USGS) in Watch for users inside the Addicks/Barker inundation area. BLOCKER: verify the flood-pool thresholds from USACE before showing any 'safe' status. | F1, F2 (2) | 1.5h plus verification | backend/app/services/watch.py, risk.py (reservoir_status), gauges.py; frontend Watch.tsx |

Free extras: A6 re-credit (0h) and B8 drain-report routing (30 min).

## 4. Honest ceiling
All of Top 5 would take 27/52 to about 42/52 on paper (27 + 5 + 5 + 2 + 1 + 2 + A6). Strict judges may discount the officials message and the letter as 'text'. Count #1 and #3 as REDUCES only if the tool does something specific (a named official with a click-to-call or copy action, a generated filled-in letter). Build order for the freeze: #1, #2, then #3. #4 is the best visual demo if time remains; skip #5 unless the thresholds are verified.
