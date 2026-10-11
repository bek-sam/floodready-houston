# Cycle 1 Research (Sat Oct 10 2026)

Method: WebSearch (standard) plus curl tests. Search summaries were not opened in full; verify before quoting in the UI. Fetched content is treated as data. No invented stats.

## 1. New or under-served problems (not in flood-problems.md A-G)

- **H1 Post-flood mold and long exposure.** Houston Health Dept focus groups (31 residents) found cost barriers led to long-term mold exposure and cleanup that did not follow guidance; Houston-3H study (347 residents) linked reported mold exposure to allergic symptoms for up to a year. Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9198619/ . Impact: any flooded household, esp. low-income; supports a mold-cleanup checklist in Recover.
- **H2 Flood-damaged cars resold.** Cox estimated up to ~500,000 Harvey cars totaled; NICB says titles are sometimes altered or washed via other states; CARFAX says several thousand slip through. Free NICB VINCheck. Source: https://www.foxnews.com/us/after-hurricane-harvey-what-will-happen-to-the-hundreds-of-thousands-of-flooded-cars . Impact: used-car buyers post-storm; easy "check a VIN" card.
- **H3 Post-flood scams and price gouging.** TX AG warns of contractors taking upfront payment, and says price gouging is barred after a governor's disaster declaration; report line (800) 621-0508. Source: https://www.texasattorneygeneral.gov/news/releases/attorney-general-paxton-warns-disaster-scams-following-texas-floods . Impact: all survivors; static card + Ask content.
- **H4 Renter repair/lease rights after a flood.** 2021 TX law requires landlords to disclose floodplain status and flooding in last 5 years (leases from 1/1/2022); Harris County Attorney advises written repair requests (713-755-6065); a landlord guide cites Prop. Code 92.0135 termination within 30 days (verify statute). Sources: https://abc13.com/amp/post/flood-warnings-texas-rental-law-landlords-renters/11399135/ , https://www.fox26houston.com/news/assessing-the-flood-damage-as-renters . Impact: renters (extends E3/B9); no credible mobile-home-specific source found, so skip that.
- **H5 FEMA denials and appeals.** Harvey: of 895,342 Texas registrants, 41% approved and 31% ineligible (Chronicle data via GovTech); Episcopal Health Foundation found low-income ZIPs more likely ineligible; Disability Rights Texas helped with appeals; appeal window was 60 days then. Sources: https://govtech.com/em/disaster/-disaster-victim-actvists-concerned-about-femas-fairness-transparency.html , https://disabilityrightstx.org/en/news/hurricane-harvey-claims-rejected-by-fema-drtx-can-help-with-appeal/ . Impact: extends G4 with an "denied? appeal" step and 60-day clock (confirm current window on fema.gov).
- **H6 Power outage plus heat.** Beryl (2024) peak 2.265M CenterPoint customers out; Texas toll at least 36 incl. heat deaths without AC. Source: https://www.pbs.org/newshour/amp/nation/hurricane-beryl-death-toll-in-texas-rises-to-36-including-more-who-lost-power-in-extreme-heat . Impact: medical-device and elderly households; not a flood, but same storm season (E1/E2).
- **H7 People experiencing homelessness near bayous.** Harris County adopted "Homelessness on the Bayou" (May 2025): at least 14 days outreach before closing flood-zone encampments; Harvey AP: many sleep under highways in low areas. Sources: https://communityimpact.com/bay-area/government/strategic-and-compassionate-harris-county-adopts-policy-to-address-flood-zone-homeless-encampments/ , https://www.huduser.gov/portal/sites/default/files/pdf/Houston-Encampment-Report.pdf . Impact: outreach workers; weak fit for a consumer app, so low priority.
- **H8 Limited-English access.** 2009 City health inquiry found many LEP residents (Chinese, Somali, Spanish, Vietnamese) not well informed about disasters; Beryl: resources mostly English/Spanish only (2025 congressional letter). Sources: https://apha.confex.com/apha/138am/webprogram/Paper230593.html , https://barragan.house.gov/wp-content/uploads/2025/07/2025-06-30-Letter-to-Chairman-Carr-and-Acting-Bureau-Chief-Nakazawa-re-Hurricane-Season-Resiliency-Roundtable52.pdf . Impact: app already has EN/ES/VI/ZH/AR; add Urdu (GLO Harvey plan lists it) as low-cost gap.
- **H9 Households without cars.** Only weak figures (~7% of Greater Houston households no gas car per UH Space City panel; 2004 census 8.7% Harris, old). A 2019 TRR study: 70% of dense block groups in floodplains. Sources: https://www.uh.edu/hobby/research/space-city-panel/csv-data-folder/space_built_environment.pdf . Impact: ACS vehicle table needed for a real number; do not cite a stat until pulled.
- **H10 Floodwater contamination.** Harvey sewage/E. coli (Texas A&M: 125x swim-safe level); boil notices were issued by 160+ TX systems. Source: https://www.cbsnews.com/news/harvey-floodwaters-mix-a-foul-brew-of-sewage-chemicals/ . Impact: reinforces G3 checklist; no live boil-notice API found.
- Searched, no credible Houston source found: schools/childcare closures, pets/livestock stats, flood-related evictions, insurance claim denial rates (NFIP).

## 2. New free data sources (tested 2026-10-10)

- **Houston Evacuation_Shelters** FeatureServer, 74 features, fields ShelterStatus(Pending/Open/Full/Closed), Name, Address, County, Capacity, Occupancy, PetFriendly. `https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services/Evacuation_Shelters/FeatureServer/0/query` (HTTP 200, no key; may be stale outside activations, check ShelterStatus). Impact: shelter finder with pet-friendly filter.
- **High_Water_Location_Demo** same org: fields FloodStatus, Need_Barricade, Barricade_Deployed; 0 features now (demo schema only). Not usable live.
- **SWM_FY26_311Cases** 77,217 records but distinct types are only missed garbage/trash pickup; not flooding. Other layers exist in the same org: `TaxDayFlood311_SZ`, `MemorialDayFlood311_SZ`, `SR311_flood_request_2015_0518_1231` (historic flood 311 by event; good for Replay overlay; not live, schemas untested).
- **Same org also lists:** `areas_with_high_flood_risk_and_low_socioeconomic_status`, `Harris_County_Multifamily_Parcels_NOT_in_a_flood_zone` (+ other counties), `RoadClosures_WaterMainBreak`, `Unsheltered_PIT_Count`, `HARRIS_COUNTY_DRAINAGE_NETWORK_ClippedCOH`. Browse: https://services.arcgis.com/NummVBqZSIJKUeVR/arcgis/rest/services?f=json (200). Impact: the multifamily-not-in-flood-zone layer directly supports renter risk (B1/E3).
- **WPC Excessive Rainfall Outlook** ArcGIS: `https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer` (200, layers "Excessive Rainfall Day 1-5", no key). Impact: day-1..5 flash flood risk category for the point (Marginal/Slight/Moderate/High); great for Watch/Home "tonight's risk".
- **NWS gridpoints** `https://api.weather.gov/gridpoints/HGX/65,97` (200): QPF and probabilityOfPrecipitation in grid data; needs User-Agent. NWS products RVF/ESF respond 200 but FFG for HGX is empty; skip flash flood guidance.
- **OpenFEMA** `https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state eq 'TX'` (200, no key). NFIP claims dataset v1 is flagged deprecated 2026-10-15 (use the replacement endpoint named in its DeprecationInformation). Impact: claim history by county for context.
- **Dead/failed:** harriscountyfws.org home is 200 but JSON endpoints guessed (`/Home/GetSiteGeoJSON`, `GetSensorList`) are 404; gis.hcfcd.org timed out; MRMS dir listings 301 (use https://mrms.ncep.noaa.gov/ GRIB2 only, too heavy for hours); CenterPoint outage page 404 from curl, no public feed confirmed.

## 3. Gaps vs app-plan.md (read pages and routers)

- **No shelter/"where to go" feature.** No router or page uses shelters; plan Module 5 mentions "I'm safe / need help" check-in, and solutions.md E2 asks for 2-1-1/shelter link-outs. Fix: new `/shelters` endpoint on the Evacuation_Shelters layer.
- **"I'm safe / I need help" family check-in absent.** No backend route; Recover has no check-in. Plan G2 (INFORMS).
- **Insurance .ics download missing** (solutions C1): grep finds no ics/calendar code in frontend or backend.
- **Printable/offline go-bag page weak.** sw.js exists, but no print stylesheet or checklist print (solutions D4, E1).
- **Document-your-stuff photo checklist not found** (plan G4 "documentation tracker", solutions G1); Recover.tsx has no local-storage tracker evidence on a quick grep.
- **Bond projects near me**, Atlas 14 slider, "safe stop" high-ground suggestions: civic.py is a 10-line static endpoint; verify it actually joins the live `Bond_CIP_Structural_CJO` layer.
- **Rainfall-last-1h badge on crossings** and **pre-trip rain/QPF** (solutions A4): not seen in crossings.py (11 lines). WPC outlook would cover this cheaply.
- **Language coverage:** 5 languages in i18n; Urdu missing relative to GLO plan.
- Caveat: pages are 110-180 lines and routers 10-60 lines, mostly thin wrappers; I did not run the app, so "missing" means not found in code by grep.

## Top 6 opportunities (ranked)

1. **Shelter finder** using Evacuation_Shelters (status, capacity, pet-friendly) on the Prepare/Recover map. Real data, tested, ~1.5h; helps evacuees incl. pet owners; fills a plan gap.
2. **WPC Excessive Rainfall risk badge** ("Day 1 risk: Slight") on Home/Watch, fed by the tested ArcGIS service. ~1h; forward-looking warning that the current app lacks.
3. **Post-flood money-safety card** (scam/price-gouging report line, flood-car VINCheck, renter rights and 30-day termination caveat, FEMA appeal reminder) as Recover content and RAG knowledge. ~1h, all sourced, no new infra.
4. **Mold and contamination cleanup checklist** (H1, H10) added to the post-flood safety checklist with sources. ~0.5h.
5. **Insurance countdown .ics download plus printable go-bag/household plan** (solutions C1, D4). ~1.5h; quick demo wins.
6. **"I'm safe / need help" check-in share link plus 2-1-1/311 link-outs** (plan G2, E2/E3); shareable pre-written text, no backend risk. ~1h.

Not recommended before demo: homeless/bayou outreach, live outage feed (no public feed), HCFWS scraping (endpoints unconfirmed), mobile-home-specific rules (no credible source).
