# Cycle 26 research: new gaps and free no-key data (tested Sun Oct 11, 2026)

Every endpoint below was called live today. "Tested" shows what came back. None of these exist in the app yet (checked with grep of backend/app, frontend/src and data/knowledge).

## 1. "What does this gauge level mean on my street?" (NWPS impact statements and crest history)
- **Problem:** Gauge chips show stage and action/minor/moderate/major. Residents cannot tell what 38 ft means. Relates to D1 and false-safety problems (B3, B10).
- **Hurts:** Anyone near a bayou, especially drivers and ground-floor residents.
- **Source:** `GET https://api.water.noaa.gov/nwps/v1/gauges/{LID}`. The app already calls `/stageflow` but not this one. Fields: `flood.impacts[{stage,statement}]` and `flood.crests.historic[{occurredTime,stage}]`.
- **Tested:**
  - HGTT2 (White Oak Bayou) has 5 impacts. Example: "At levels above 38.5 feet, major lowland flooding continues as the I-45 main lanes north of I-10 are inundated."
  - BAKT2 (Barker) has 10 impacts, including "Pool of Record (Harvey)" at 101.56 ft.
  - ADDT2 has 11 historic crests; the Harvey crest was 109.09 ft on 2017-08-30.
  - HSIT2, HFFT2 and MBVT2 have 0 impacts, so the UI must handle an empty list.
- **Feature:** On each gauge card, show "At the current stage: <nearest impact below>" and "Next impact at X ft", plus "Harvey crest was N ft above today's level". All text is NWS-sourced. Cache `data/gauges.json` impacts offline.
- **Effort:** 1.5 h. **Demo value:** high (links the live gauge to Harvey).

## 2. "How rare is this rain?" (observed radar rainfall vs NOAA Atlas 14)
- **Problem:** Warnings say "heavy rain" but give no sense of severity. The app has a forecast (`/rain24`) but no observed totals. Relates to D4 and B4 (outdated rainfall data).
- **Hurts:** Everyone, during and after a storm.
- **Source A (observed):** MRMS radar QPE image service, no key. Identify call:
  `https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer/identify?geometry={"x":-95.37,"y":29.76,"spatialReference":{"wkid":4326}}&geometryType=esriGeometryPoint&renderingRule={"rasterFunction":"rft_24hr"}&returnGeometry=false&f=json`
  - Rendering functions are `rft_1hr, 3hr, 6hr, 12hr, 24hr, 48hr, 72hr`.
  - Tested: returns `properties.Values:["0"]` today (no rain) and catalog item `conus_QPE_24H` with `idp_validendtime`.
  - The service description says units are inches. The value is radar-only (1 km), so label it "radar estimate".
  - Without the explicit `renderingRule` and `sr`, the call returned `NoData`.
- **Source B (return periods):** `https://hdsc.nws.noaa.gov/cgi-bin/new/fe_text_mean.csv?lat=29.76&lon=-95.37&type=pf&data=depth&units=english&series=pds`
  - Needs `curl -L`: the old `/cgi-bin/hdsc/new/` path returns a 301.
  - Tested: returns NOAA Atlas 14 Vol. 11 v2 CSV. Example for downtown: 24-hr 1-yr 3.80 in, 10-yr 8.74 in, 100-yr 17.0 in. 3-hr 100-yr 8.59 in.
- **Feature:** "Last 24 h: 6.2 in of radar rain, about a 10-year storm here." Compare the observed total to the Atlas 14 row of the matching duration. Wording: "roughly a 1-in-N-year rainfall, not a flood prediction."
- **Accuracy trap:** do not use Open-Meteo archive to compare with Harvey. Its reanalysis gave only 19.6 in for 26-29 Aug 2017 at downtown, which understates the real event. Use MRMS or Atlas 14 only.
- **Effort:** 2 h. **Demo value:** high; works live, and `?simulate=storm` can fake a number.

## 3. "What FEMA aid actually looked like in my ZIP" (OpenFEMA individual assistance, Harvey)
- **Problem:** Aid is slow and unevenly granted, and residents do not know what to expect. Relates to G4 and the C-group insurance gap.
- **Hurts:** Renters and owners deciding whether to register after a flood.
- **Source:** `https://www.fema.gov/api/open/v2/HousingAssistanceOwners?$filter=disasterNumber eq 4332 and zipCode eq '77096' and county eq 'Harris (County)'` and the same with `HousingAssistanceRenters`. Fields: `validRegistrations, totalInspected, approvedForFemaAssistance, totalApprovedIhpAmount, averageFemaInspectedDamage`.
- **Tested for ZIP 77096 (Harris rows):**
  - Owners: 2,428 registrations, 1,785 approved, $9,689,946 total approved, average FEMA-inspected damage $17,435.
  - Renters: 3,722 registrations, 1,624 approved (44%), $4,820,243.
  - Each ZIP returns several rows, one per county the ZIP touches. Filter by county or sum.
- **Companion:** `DisasterDeclarationsSummaries?$filter=state eq 'TX' and designatedArea eq 'Harris (County)' and declarationDate gt '2015-01-01'` gives these declarations. The list is after de-duplicating by `disasterNumber`:
  - Flooding: 4223 (2015), 4245 (2015), 4269 (Apr 2016), 4272 (Jun 2016), 4466 (Imelda 2019), 4781 (May 2024).
  - Hurricane: Harvey 4332 (2017), Hanna 3530, Laura/Marco 3540 (2020), Beryl 4798 (Jul 2024).
  - Winter storm 4586 and COVID-19 declarations also appear.
  - "Harris County has had 6 flood-declared disasters since 2015" is checkable. Count by `incidentType` and `declarationTitle`, not by guesswork.
- **Feature:** On the Recover page and in `/compare`: "In Harvey, 44% of renter registrations in 77096 were approved. Register at DisasterAssistance.gov even if you think you won't qualify." Add the repeat-declaration count to the flood-history card.
- **Caveats:** Registrations are not the same as flooded homes. Source is FEMA Harvey data, not a prediction. Zip-level counts under about 10 may be masked or 1-row noise.
- **Effort:** 1.5 h. Reuse the existing OpenFEMA client from `/zip-insurance`.

## 4. Neighborhood risk and vulnerability context (FEMA National Risk Index, tract level)
- **Problem:** Risk is shown by FEMA zone and Harvey only. No view of who in the area is most exposed, and no inland-flood score that goes beyond the FIRM. Relates to B1 and E1.
- **Hurts:** Low-income and elderly neighborhoods, which have weaker recovery capacity. Also useful for NGOs and judges who ask about equity.
- **Source:** `https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/National_Risk_Index_Census_Tracts/FeatureServer/0/query` with `geometry=lon,lat`, `geometryType=esriGeometryPoint`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, `returnGeometry=false`, `outFields=TRACTFIPS,IFLD_RISKR,IFLD_EALR,IFLD_AFREQ,RESL_RATNG,SOVI_RATNG,SOVI_SPCTL,RISK_RATNG,POPULATION`.
- **Tested (Meyerland, -95.4698,29.6870):** tract 48201420800, `IFLD_RISKR` "Very High", `IFLD_EALR` "Very High", `IFLD_AFREQ` 5.14 events/yr, `RESL_RATNG` "Very Low", `SOVI_RATNG` "Very Low", `RISK_RATNG` "Relatively High", population 2,274.
- **Note:** `IFLD` is the NRI inland flooding code. `CFLD` is coastal. The field `RFLD` does not exist in this layer. Always request fields by name; an invalid `outFields` returns a 400, as a wrong first attempt showed.
- **Feature:** A one-line "Neighborhood context" chip on Risk or `/compare`: "Inland flood risk: Very High. Community resilience: Very Low. Social vulnerability: Very Low (FEMA NRI, tract-level)." Include the explainer that the rating is a statistical index, not your house.
- **No-key warning:** the Census ACS API now returns "Missing Key" and a 302 to a signup page (tested), so car-ownership and renter shares are not available without a key. Use NRI SOVI instead. The Census geocoder (tract lookup) still works without a key.
- **Effort:** 1 h.

## 5. Extend the Rainfall Outlook to Days 2-5 ("storm-watch timeline")
- **Problem:** The app shows only the Day 1 WPC Excessive Rainfall Outlook. The 30-day insurance wait and "prepare early" logic need a multi-day heads-up.
- **Source:** same MapServer the app uses: `https://mapservices.weather.noaa.gov/vector/rest/services/hazards/wpc_precip_hazards/MapServer/{1..4}/query`
  - Layers: 0 = Day 1, 1 = Day 2, 2 = Day 3, 3 = Day 4, 4 = Day 5.
  - Query fields: `outlook, valid_time, issue_time, dn`.
- **Tested:** layers 1 and 2 respond with the full schema and `features: []` today (no risk area over downtown, which is correct for a dry week). A populated response was not seen, so test against a stormy day or use `?simulate=storm`.
- **Feature:** A 5-day strip (Day 1-5) with category chips. Auto-trigger the existing "Prepare" nudge when any day has Slight or higher. Reuse the label mapping from `outlook.py`.
- **Effort:** 1 h.

## 6. Plain-language "what the warning level means" for NWS flash-flood tiers (verify first)
- **Problem:** People ignore a Flash Flood Warning because they cannot tell routine from Considerable or Catastrophic. Relates to D3 and D5.
- **Source status:** The three tiers (Base / Considerable / Catastrophic) are confirmed by NWS rollout material (https://www.weather.gov/media/notification/pdf2/scn19-101wea_floods.pdf). Considerable and Catastrophic trigger Wireless Emergency Alerts.
- **Not verified:** I could not confirm the exact `parameters` key on api.weather.gov (live alerts today had only Coastal Flood Advisory, Flood Warning and Rip Current; no Flash Flood Warning to inspect). `alerts.py` currently reads only event, severity, headline and description (line 14), so it would drop any such tag.
- **Feature (if the field exists):** Highlight "Considerable" or "Catastrophic" with a red banner and copy "This is the strongest tier. Call 911 if trapped." If absent, fall back to a regex on the description text.
- **Effort:** 1 h plus verification during the next real FFW. Lowest confidence of the list.

## Negative findings (do not spend time here)
- Harris County Flood Warning System (harriscountyfws.org) has no documented API. Only bulk Document Library downloads and Excel export, per https://harriscountyfws.org/FAQs. A third-party scraper exists (https://github.com/dcbark01/HouFloodScraper) but is unofficial.
- HCFCD MAAPnext draft flood-map data: no public FeatureServer found (https://maapnext.harriscountytx.gov/about). Drafts are non-regulatory and not open for appeal.
- NWS products API for WPC mesoscale discussions (`/products/types/MCD/locations/WNH`) returned an empty list today, so it is not a reliable feed.
- `api.water.noaa.gov` stage-flow forecast returned `data: []` for HGTT2 when not in flood, so forecast crest features only appear during an event.

## Accuracy risks in the app's stated facts
1. **30-day insurance wait has exceptions the countdown ignores.** `backend/app/services/insurance.py` (line 12) and `data/knowledge/insurance-30-day-and-gap.md` state the wait with no exceptions. FloodSmart says (https://www.floodsmart.gov/get-insured/buy-a-policy): no wait with a mortgage making, increasing, extending or renewing; no wait when changing coverage at renewal; a one-day wait for property in a newly designated high-risk zone (bought within 12 months of the update); a one-day wait after wildfire-caused flooding. Add one line: "Exceptions exist (for example, buying with a mortgage). Ask your agent." High-priority fix; an uninformed buyer could be told they are uncovered when they are covered.
2. **Flood-bond figures are stale.** Facts say "By March 2025, 43 of 181 projects complete, $864M of $2.5B spent" (auditor memo, June 2025). Community Impact reports a fall-2025 restructuring: 54 packages completed, 75 of the remaining 116 moving forward, 26 paused, 15 closed as not feasible, and a quarterly dashboard (https://communityimpact.com/cypress/government/a-new-vision-harris-county-restructures-2018-bond-projects-and-funding/). The app already says "By March 2025", which is honest, but add "restructured fall 2025; see the HCFCD dashboard" to avoid implying it is current.
3. **MAAPnext timeline.** Knowledge says new maps in "about 2-3 years". Officials now say the maps may not be final until 2028 (https://communityimpact.com/cypress/government/harris-county-officials-publish-draft-fema-flood-map-data-talk-next-steps/). Say "possibly 2028" instead of a relative number that ages.
4. **Do not pair Open-Meteo archive rainfall with Harvey.** See item 2.
5. **Quoted 92% figure.** Already handled as a quote in `insurance-30-day-and-gap.md`; confirm the UI never prints it as a statistic.
6. **USGS legacy `waterservices` decommission** is scheduled for Q1 2027 (https://waterdata.usgs.gov/blog/api-waterservices-decom/). No `waterservices` calls were found in `backend/app` or `scripts` by grep, so there is no action unless the data agent's scripts use it.

## Recommended order for a 2 h/dev sprint
1. Insurance exceptions fix (10 min, accuracy).
2. Item 1 gauge impacts (1.5 h).
3. Item 2 "How rare is this rain" (2 h).
4. Item 3 FEMA aid by ZIP (1.5 h).
5. Item 4 NRI chip (1 h).
6. Item 5 outlook days 2-5 (1 h).
7. Item 6 only after verifying the field.
