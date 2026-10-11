# Cycle 27 research: under-served gaps + fact-check (tested Sun Oct 11, 2026)

grep of data/knowledge, frontend/src and backend/app found no mention of: critical-care/power-dependent, generator/CO, mobile/manufactured homes, or homeless/unhoused. emPOWER is not used anywhere.

## A. Gaps (buildable <= 1.5 h)

### A1. Power-dependent medical devices in an outage (oxygen, vents, dialysis)  [highest value, ~1 h]
- **Gap:** knowledge says "have a power plan" but gives no concrete step or local number. Floods cause outages; CO from generators is the usual killer afterwards.
- **Data (tested, no key):** HHS emPOWER public ArcGIS FeatureServer
  `https://services2.arcgis.com/ZQ4jTQn6k7VPXEwO/arcgis/rest/services/HHS_emPOWER_REST_Service_Public/FeatureServer`
  - ZIP layer 1: `GET {base}/1/query?where=Zip_Code%3D'77096'&outFields=Zip_Code,Medicare_Benes,Power_Dependent_Devices_DME,O2_Services_Any_DME,Facility_ESRD_Dialysis_Any_DME&returnGeometry=false&f=json`
    -> tested 77096: `Medicare_Benes 5601, Power_Dependent_Devices_DME 201, O2_Services_Any_DME 31, Facility_ESRD_Dialysis_Any_DME 40`.
  - County layer 2 (`where=County_FIPS_Code='201' AND State_FIPS_Code='48'`) -> Harris: 672,080 Medicare beneficiaries, 28,811 on power-dependent devices, 4,366 O2.
  - Layers 5/9/13/17/21 are the dialysis/O2/home-health/hospice breakdowns. Max 2,000 rows. Label as "Medicare beneficiaries only; counts, not people's locations". Catalog: https://catalog.data.gov/dataset/hhs_empower_rest_service_public ; map: https://empowerprogram.hhs.gov/empowermap
- **Guidance (authoritative):** Texas PUC Critical Care / Chronic Condition residential designation (physician certifies; PUC Subst. Rule 25.497; form copy https://www.ercot.com/files/docs/2024/01/17/PUC-Critical-Care-Form.pdf). It does NOT guarantee uninterrupted power or faster restoration (CenterPoint/KHOU: https://khou.com/article/news/investigations/medical-devices-power-outage-data/285-275759d6-4422-4701-87fd-7c24e2481bf9). Generator CO rule (CDC): outdoors, more than 20 ft from windows/doors/vents, battery CO alarm; https://www.cdc.gov/carbon-monoxide/about/index.html . Existing STEAR + CDC dialysis lines stay.
- **Feature:** "Power-dependent?" card in Prepare/Special needs: ZIP-level emPOWER count (context), 4-step checklist (ask doctor to certify, apply with your utility, charged backup + battery for 3 days, STEAR/211), CO generator warning, "call 911". Fallback: static text if the service fails. Sources shown.

### A2. Generator / CO safety after a flood (all households, esp. seniors)  [~20 min, bundle with A1]
- CDC source above. Add a knowledge card `power-outage-and-generators.md` so Ask can answer it. Symptoms per CDC: headache, dizziness, weakness, upset stomach, vomiting, chest pain, confusion; "call 911 / leave the house".

### A3. Mobile / manufactured-home residents  [~30 min, text only]
- **Gap:** none in app. Guidance (FEMA): never take refuge in a manufactured unit during high winds or floods; evacuate immediately when officials say so; flash-flood warning -> move to higher ground. Sources: https://www.fema.gov/print/pdf/node/695591 and https://www.fema.gov/zh-hans/print/pdf/node/691040 (both are FEMA temporary-housing fact sheets; wording is written for FEMA units, so phrase as "FEMA advises occupants of manufactured housing..."). The Ready.gov "mobile homes will not survive a Category 5" line is only from news reprints, so do not cite it.
- **Data caveat:** Census ACS B25024_010E (mobile homes per tract/ZIP) would give a "share of mobile homes in your area" chip, but **api.census.gov now returns "Missing Key"** (tested: needs free key). Violates the no-key rule; skip, or prebuild a Harris tract table once offline with a key.

### A4. Non-English renters / seniors alone (data)  [only if time; needs key]
- ACS variables confirmed to exist (variables.json): `B16002_004E` (Spanish, limited-English household), `B11007_*` (households with 65+, by size), `B25003_003E` (renter). Same Census key problem as A3, so recommend NOT building. The app already has 5-language UI, renter disclosure (Prop. Code 92.0135) and the FEMA NRI social-vulnerability chip (/nri), which covers this need acceptably.

### A5. Unhoused people  [~15 min, text only]
- No authoritative free dataset or Ready.gov page found (ready.gov/homeless-shelter is 404). Do not invent. Minimal safe step: add to the 211/311 card "If you have no stable housing: call 2-1-1 for shelter and evacuation transportation (211 Texas lists shelter assistance and extreme-weather shelters, per existing special-needs card); never shelter under bridges/in creek beds during rain (NWS Turn Around Don't Drown)". The 211 part is sourced (https://www.211texas.org/); the NWS line needs a URL check before use.

## B. Fact-check (10 + 3 extras)

Verified correct (fetched source today):
1. 56% of Harvey fatalities over 50, 29% over 65, 70% male (NHESS, https://nhess.copernicus.org/articles/18/1073/2018/): OK.
2. 4 deaths lack of medical treatment, 4 electrocution; "more than 120,000 rescued": OK (same page).
3. 5,138 of ~14,000 homes in reservoirs flooded; "4,000 built after Allison": OK, source says "at least 4,000" (https://projects.propublica.org/graphics/harvey-reservoirs).
4. Harris "2nd largest population of older adults with disabilities" (attributed to Census): OK (https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system).
5. STEAR: stear.texas.gov, 2-1-1, video relay 877-541-7905, "doesn't guarantee assistance": OK (https://tdem.texas.gov/stear).
6. CDC kidney: NKF 1-855-653-2273, KCER 1-866-901-3773, register with water/power companies, 3-day diet: OK (https://www.cdc.gov/kidney-disease/caring/).
7. 36% of flooded Harris homes insured; "more than 300,000 vehicles": OK (https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county). Source says "a little more than 300,000".
8. "43 of 181 projects complete" (June 2025): matches https://www.fox26houston.com/news/harris-county-flooding-projects-budget-shortfall . **Wording caveat:** the 181 are "Bond IDs" (groupings of ~400 projects, per Houston Press via search), so say "43 of 181 bond project groups" not "projects".
9. Restructure 54 completed / 75 active / 26 paused / 15 not feasible of 116 remaining: OK, but these count project **packages**, not projects; "fall 2025" = Sept 18, 2025 vote (communityimpact search snippet; county release https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond). The cited Cypress article page itself lists only 4 active/5 paused, so cite the Sept 18 county release or the Community Impact bond article from search instead. Also note the later $400M shortfall (reduced from ~$1.3B).

Wrong / unsupported:
10. **reservoirs-and-dams.md + civic.json: "rated 'extremely high risk'"** is NOT in the cited Texas Tribune article. The Corps text there is "studies since 2004 ... a high risk of failure due to seepage and piping". Fix: drop "extremely high risk" or cite a source that has it. Also the article says repairs "more than $100 million ... not all completed" (OK).
11. **reservoirs-and-dams.md: "167,000 acres were developed in the decade after Allison (ProPublica)"**: not found on the cited ProPublica page (the page gives ~24,500 acres bought by the Corps and ~8,000 more that could flood). Remove or re-source. (Source check done on /graphics/harvey-reservoirs; the cited /graphics/harvey page was not fetched.)
12. **civic.json + renters-and-buyouts.md: "Neither the city nor the county requires flood disclosure to buyers" / "to buyers and renters"**: true of 2017 ProPublica reporting but misleading today. Texas has required a written landlord flood notice since Jan 1 2022 (Prop. Code 92.0135; already in tenant-flood-disclosure.md, so the files contradict each other). Sellers must also disclose floodplain/flood-pool/reservoir status on the seller's disclosure form since SB 339 (2019): https://capitol.texas.gov/tlodocs/86R/analysis/pdf/SB00339S.pdf . Fix: "As of 2017 ProPublica reporting, neither Harris County nor Houston required...; Texas law now requires landlord notice (92.0135) and a seller's disclosure." Add the "plat note" qualifier (Barker only per source).
13. fema-aid-and-recovery.md: "vehicles flooded: more than 300,000" fine; "Harvey 120,000 rescued" attributed to NHESS fine.

Not checked (PDF text not extractable here): auditor memo figures $864M spent, $165M of $834M FRT, $317.5M vs $187.3M quartiles. Fox 26 confirms 43/181 and ~$1.3B shortfall (2.5B bond) only. Someone should open the memo PDF manually before demo, or soften to "per the county auditor's June 2025 memo".
