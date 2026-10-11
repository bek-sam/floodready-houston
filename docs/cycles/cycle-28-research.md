# Cycle 28 research: moving INFORMS/NONE toward REDUCES

Baseline: `docs/cycles/cycle-24-coverage.md` (33 REDUCES / 17 INFORMS / 2 NONE). Tests run Sun Oct 11 2026 ~10:50 UTC with curl and a `FloodReadyHouston/0.1` User-Agent. Anything marked UNTESTED was not verified live. Do not build on it without a check first.

## 0. Coverage recount note
- **A9 (vehicle losses)**: cycle 24 says "no move-your-car feature exists". Cycle 25 then shipped `/parking/check` and `/rain24`. A9 probably qualifies as REDUCES now. Re-verify in the UI, then count it (34).

## 1. NONE problems

### D7: data sources are changing (USGS WaterServices decommission, Q1 2027)
- Why weak: `#status` (`routers/status.py`) is monitoring, not user-facing.
- Honest verdict: structural, a build-side risk. No app feature can reduce harm for a resident. Do not claim it in the pitch. The only real action is to migrate any remaining legacy `waterservices` calls to the OGC API (`https://api.waterdata.usgs.gov/ogcapi/v0/`), which is engineering hygiene.
- Effort: 0.5h to grep for `waterservices`. User-facing: none.

### F3: development keeps paving over land that absorbed water
- Why weak: nothing in the app addresses development or paving.
- Honest verdict: policy problem. The only resident-level actions are (a) check a new-build home or rental before committing and (b) take part in public decisions.
- Proposed feature (1h): "Buying/renting new construction near you" checklist, shown when the address is in the SFHA or Harvey extent. It tells the user to ask for the elevation certificate, to compare it with nearby Harvey high-water marks (`/api/hwm`, tested earlier), and to ask about detention. It also links the MAAPnext page, which loaded with HTTP 200: `https://www.hcfcd.org/MAAPnext`.
- A pre-filled public comment or meeting calendar would need a sourced agenda feed. I did not find or test one, so I do not propose it.
- Effort: 1h. Source for the checklist wording: FEMA elevation certificate guidance (UNTESTED URL, find at fema.gov before shipping).

## 2. Six weakest INFORMS

### F1 / F2: reservoir risk and releases (Addicks/Barker)
- Why weak: only an explainer and a reservoir-area flag (`civic`).
- Proposed feature: **"Reservoir pool vs your ground"**. Show the live Addicks pool level with its action (93 ft) and minor (96 ft) thresholds and the Harvey crest (109.09 ft). If the user's ground elevation (`/risk elevation_ft`) is within about 15 ft below the pool, add a "pool is X ft below your ground; Harvey peaked Y ft above it" line and a watch prompt. Caveat required: the pool datum (likely NGVD29) may differ from EPQS NAVD88, so show it as approximate and say "not official guidance. Call 911 and follow evacuation orders."
- Tested live: `GET https://api.water.noaa.gov/nwps/v1/gauges/ADDT2` returned `status.observed.primary=83.89` (ft), `secondary=6.94` (kcfs), `validTime=2026-10-11T10:15:00Z`, `flood.categories.action.stage=93`, `minor.stage=96`, and a historic crest `stage=109.09` at `2017-08-30`. `GET .../gauges/ADDT2/stageflow` returned `observed.data[]` with `primary` (pool ft) at 15-minute intervals. `usgsId=08073000`.
- The app already carries ADDT2 in `data/gauges.json` and `gauge_impacts.json`, so this reuses existing plumbing. Barker (BRKT2) was NOT confirmed: my call was cut off before I saw the output. Check it.
- Effort: 1.5h. Turns F2 into REDUCES (an address-specific alert and watch trigger). F1 stays structural (dam condition), so it remains INFORMS.

### E5: critical services shut down
- Why weak: the dialysis finder only says "confirm storm closures by phone".
- Proposed feature: **"Is IAH/Hobby open?" plus a closure line** in Watch/Drive. The FAA feed lists airport closures.
- Tested live: `GET https://nasstatus.faa.gov/api/airport-status-information` returns XML with `<Airport_Closure_List><Airport><ARPT>`, `<Reason>`, `<Start>`, `<Reopen>`. Today IAH, HOU and EFD are not listed (so "no closure reported"). Filter on `ARPT in {IAH, HOU}`. The feed is NAS closures, not weather-specific, so word it "FAA reports closed/not reported closed".
- Transit and hospital closures have no tested feed. METRO's GTFS-RT URL `gtfs.ridemetro.org` returned a different site, so UNTESTED and not proposed. Keep the hospital part as a "call ahead" with the dialysis tel: links (already built).
- Effort: 1h. Partial credit only. E5 stays INFORMS unless a facility-level feed turns up.

### E3: renters displaced by buyouts
- Why weak: the tenant letter covers flood notice and lease rights, not buyout displacement.
- Proposed feature: **"Buyout displacement rights" card for tenants** inside the existing `/buyout-area` flow. It says that displaced tenants may be entitled to relocation assistance under the federal Uniform Relocation Act (49 CFR Part 24) when a federally funded acquisition displaces them. It adds a letter template that asks the program for a written relocation notice and advisory services, and tells the user to keep their lease and rent receipts.
- Tested: the eCFR versioner API returns the definition of "Displaced person" for 49 CFR 24.2 (needs `Accept-Encoding: gzip`): `https://www.ecfr.gov/api/versioner/v1/full/2026-10-01/title-49.xml?part=24&section=24.2`. The county program page is cited in `flood-problems.md` E3 (`https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/`) and was not re-fetched. Whether a specific buyout is federally funded must be confirmed with the program, so the copy must say "may be entitled; ask".
- Effort: 1h. Moves E3 to REDUCES (a concrete action with a sourced right).

### C4 / C5: rising premiums, no affordability help
- C5 is structural (policy): no NFIP affordability program exists, so no app can create one. Honest action: a "ways to lower your premium" card (elevation certificate, higher deductible, mitigation credits). I did NOT test a FEMA/FloodSmart URL. Only ship it with a verified source.
- C4 (trend): the proposal was ZIP premium by policy year from OpenFEMA to show the trajectory. Tested: v2 `FimaNfipPolicies` still answers but its metadata says it is deprecated, frozen at 2026-06-01, and removed by **2026-10-15** (replacement `https://www.fema.gov/openfema-data-page/nfip-redacted-policies-v3`). My guessed v3 endpoint name `FimaNfipPoliciesV3` returned a 404 page, so the correct name is UNTESTED. The app's `services/zipinsurance.py` already tries v3 for claims, so check how it handles policies after Oct 15.
- Effort: 2h including finding the endpoint. Even then it stays a distribution, so INFORMS. Not recommended for today.
- Urgent side finding: the v2 policies dataset disappears on Oct 15. Confirm the `premiums` field degrades to the snapshot instead of failing.

### B4 / B5: outdated maps, new maps years away
- Why weak: a static card.
- Proposed feature: **"Is my address in the draft MAAPnext floodplain?"** next to the effective FEMA zone. This would change the buy-insurance decision (B5 draft maps are not regulatory but signal risk).
- Tested: `https://www.hcfcd.org/MAAPnext` loads (HTTP 200). I did not find a queryable draft-map layer URL, so there is no confirmed data source. Do not build this until an ArcGIS/FeatureServer URL is found and tested. If one exists, the effort is 1.5h.
- Fallback: a link plus the already sourced caveat "draft, not regulatory".

### D6: live roadway flood feed not public
- Honest verdict: structural. TranStar says live feeds require contacting them (`https://traffic.houstontranstar.org/api/api_doc.aspx` loads and states this). The TxDOT DriveTexas endpoint `https://drivetexas.org/api/conditions.geojson` returned HTTP 500 today, so it is not usable. Community reports (already built) are the realistic substitute. Suggest a lead email to TranStar as a post-hackathon action. No feature today.

## 3. Ranking by value per hour
1. F2 reservoir pool vs your ground: 1.5h, tested data, real address-level action.
2. E3 buyout tenant rights: 1h, sourced law, concrete letter.
3. E5 FAA closure line: 1h, tested feed, partial.
4. A9 recount: 0.25h, probably already done.
5. F3 new-construction checklist: 1h, needs a FEMA source.
6. Everything else (D7, D6, C5, F1, B4/B5) is structural or blocked on data; say so and do not claim it.

Realistic ceiling: 33 to about 36 of 52 (A9, F2, E3), not more.
