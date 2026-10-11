# Houston Flood Problem Catalog

Compiled 2026-10-11 for FloodReady Houston. 52 original problems (A1-G6) plus 11 problems added from the build-cycle research (IDs with `-new`). Total: 63.

## How to read this

**How the problems were found.** The 52 original problems come from `flood-problems.md` (about 30 sources read in full on 2026-10-10: peer-reviewed papers, county and federal pages, a county auditor memo, ProPublica/Texas Tribune investigations, local news). The `-new` problems were found during the 37 build cycles (`docs/cycles/cycle-*-research.md`) while auditing who the app still fails. Examples are power-dependent residents, manufactured homes, flood-damaged cars, FEMA denials and the NFIP proof-of-loss deadline. `research-brief.md` supplies the event history and other numbers.

**How sources were checked.** On 2026-10-11 I re-fetched 36 source URLs and compared each claimed number or quote with the page text. Marks:
- ✓ = the fact was found on the page (checked 2026-10-11).
- ✓* = found, but the app's wording needed a correction (stated in the row).
- ✗ = not found on the page, or contradicted by it.
- ? = the page could not be read (binary PDF, truncated page, HTTP 403, redirect). The claim is not confirmed.
- (c#) = taken from cycle-# research and **not** re-fetched today.

Wikipedia and news are marked as secondary. Government, peer-reviewed and official data are preferred wherever they exist.

**"Solvable by an app?"** Yes = an app can directly reduce the harm. Partly = it informs or routes, but the root cause stays. No = the cause is policy, funding or engineering.

**Corrections applied** (from cycle 27 and from today's checks) are marked **[CORRECTED]**. They are listed again at the end.

---

## A. Drivers die in flooded roads and underpasses (9)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| A1 | **Driving into floodwater is the top killer.** Most Texas flood deaths happen to people in vehicles. Roads look passable at night or in rain, and depth is hard to judge. | 77% of Texas flood fatalities (1959-2008) came from driving into flood water; 840 Texas deaths 1959-2009, 3x the next state (TMC dissertation: https://digitalcommons.library.tmc.edu/dissertations/AAI1470211) | ✓ (the abstract says "1959 through 2009" for the 840 but "1959 and 2008" for the study period) | Yes: personal route warnings act before the driver reaches the water |
| A2 | **Harris County leads the state in vehicle flood deaths.** Houston's flat terrain and underpasses make it worse than Dallas even though Dallas floods often. | Harris County "had the most vehicle related deaths"; Dallas "almost seven times less" (LSU thesis: https://repository.lsu.edu/gradschool_theses/5466) | ✓ | Yes: local, route-level risk |
| A3 | **"Turn Around Don't Drown" has no measured effect.** Generic slogans do not change behavior, so warnings must be personal and timely. | "not a convincing amount of evidence that the slogan has reduced deaths" (LSU thesis, same URL) | ✓ | Yes: personalized, timed alerts instead of a slogan |
| A4 | **The same underpasses keep killing.** Known death spots stay open and unmarked for drivers. | "Three of the deaths were at the same Houston underpass" (April 2016) (Observer-Reporter, secondary news: https://cs.observer-reporter.com/news/2016/apr/21/driver-deaths-spur-investigation/) | ✓ | Yes: crossing map plus route check |
| A5 | **Low-water crossings are not mapped or communicated.** Dangerous spots outside the floodplain are not delineated for the public. | The paper says high-hazard areas outside the floodplain, "such as low water crossings, have not been adequately delineated or communicated to the public" (an inference by the authors, not a count). NHESS 2018: https://nhess.copernicus.org/articles/18/1073/2018/ | ✓ | Yes: crossings dataset (no official underpass dataset exists) |
| A6 | **Physical warnings are incomplete.** Sensor and flashing-light systems were half-built. | Early-warning system planned at 27 locations, sensors and lights at 19; Judge Emmett: "There's no question that not enough has been done." He called two of the deaths "completely preventable" (Observer-Reporter, same URL) | ✓* (the quote refers to two of the deaths at that underpass, not all of them) | Partly: reports and route flags fill gaps, but cannot build barriers |
| A7 | **Drivers go around barricades.** A warning has to reach the driver before the water does. | June 2026: "Some vehicles became stuck under bridges and had to be towed" (Click2Houston, secondary: https://www.click2houston.com/news/local/2026/06/16/this-is-not-over-harris-county-braces-for-more-flooding/). The gate-crash detail is from Observer-Reporter. Emmett said he did not know if any system can stop a driver who goes around a barricade. | ✓ | Yes: pre-trip route alert |
| A8 | **Harvey drownings were in and around vehicles.** | The paper: "Most fatalities occurred due to drowning (81 %), particularly in and around vehicles." In the body, only 21 of 57 drownings were vehicle-related. **[CORRECTED]** 81% is drownings overall, not vehicle deaths. At least 70 deaths in total. (NHESS 2018, same URL). The "family of 6 in a van" detail was not re-checked. | ✓* | Yes |
| A9 | **Huge vehicle losses.** Flooded cars mean lost jobs and transport, and many are towed. | "A little more than 300,000 vehicles were flooded" in Harris County in Harvey (Community Impact: https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county). Imelda: 1,600 towed in Houston (Wikipedia, secondary: https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019)). **[CORRECTED]** The ">1,000 vehicles caught" figure refers to I-10 between Winnie and Orange, not Houston. | ✓* | Yes: park-my-car check, alerts |

## B. Official maps give a false sense of safety (11, plus 1 new)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| B1 | **Most flooding happens outside FEMA zones.** Residents outside the mapped floodplain think they are safe. | "A little less than half of the homes that flooded in the county were located outside of the 100- and 500-year floodplains" (Community Impact, URL under A9). Only 22% of the 37 Harris County casualties were inside the 100-year floodplain (NHESS). Use the county figure, not KPRC's ~75%. | ✓ | Yes: address-level check beyond FEMA |
| B2 | **Low-risk zones still file many claims.** | "More than 25% of all flood insurance claims come from properties located in moderate- or low-risk areas" (HCFCD MAAPnext: https://maapnext.harriscountytx.gov/Understand-Your-Risk) | ✓ | Yes |
| B3 | **"Not in a flood zone" misleads.** FEMA lines are insurance math, not water physics. | Rice researcher Yilei Yu: "not in a flood zone" is a dangerous misnomer; map lines are "often actuarial, not physical" (Rice News: https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk) | ✓ | Yes |
| B4 | **The maps in force are outdated.** The effective maps predate Atlas 14 rainfall. | The article cites "a more than 30% increase in rainfall rates" in Harris County and says the old maps used post-Allison (2001) data (ReduceFlooding: https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/). **[CORRECTED]** The page does not say the 30% is measured against the 2007 maps. The "rearview mirror" quote was not re-checked. | ✓* | Yes: show draft and old context |
| B5 | **The new maps are years away.** | HCFCD spokesperson: the drafts are "not final, not regulatory, and not part of FEMA's formal public appeal and comment process" (ReduceFlooding, same URL). **[CORRECTED]** Timeline: the article gives both "a year or two" and "two to three years". Community Impact says possibly 2028 (c26). The old "cannot be used for insurance decisions" wording is not on the page, and the article says buyers can use the drafts to check risk. | ✓* | Partly: explains status but cannot speed up adoption |
| B6 | **The draft map viewer is hard to use.** | "The map doesn't work on cell phones. You must use a desktop or laptop" (ReduceFlooding, same URL). The "shades and dots" and "foot or two wide" remarks were not re-checked. | ✓ (partly) | Yes: mobile-first address view |
| B7 | **Risk depends on where the storm tracks.** | A Clear Creek simulation: about 3,600 homes would flood; shifting the storm center gives "more than 13,000" (Click2Houston, secondary: https://www.click2houston.com/news/local/2026/04/21/new-maps-reveal-hidden-flood-danger-across-houston/). Both are modeled results. The Rice release gives only the 13,000 figure. | ✓* | Yes (illustrative scenarios) |
| B8 | **Drain and sheet-flow flooding away from bayous.** | Flooding "surpasses the ability of the local drainage infrastructure" (MAAPnext, B2 URL). **[CORRECTED]** The earlier quote "inadequate or overloaded storm drainage systems" is not on that page. harriscountyfws.org/Help was not readable (?). | ✓* | Partly: hard to model street-level |
| B9 | **No disclosure to buyers and renters (as of 2017 reporting).** People learn about flood risk only after moving in. | "When I started to rent this house, nobody told me." As of the ProPublica reporting, neither Harris County nor Houston required a disclosure; Fort Bend added a one-sentence plat note (Barker area), "buried in plat documents" (ProPublica: https://projects.propublica.org/graphics/harvey-reservoirs). **[CORRECTED]** Texas now requires a written landlord flood notice (Prop. Code 92.0135, from 1 Jan 2022) (c1: https://abc13.com/amp/post/flood-warnings-texas-rental-law-landlords-renters/11399135/). SB 339 (2019) adds seller disclosure of floodplain/reservoir status (c27: https://capitol.texas.gov/tlodocs/86R/analysis/pdf/SB00339S.pdf; PDF not readable today, ?). | ✓* / ? | Yes: tells the user what they are owed |
| B10 | **People are caught unaware.** | June 2026: a UH-Downtown student said "I had no idea there was a flood" (Click2Houston, A7 URL) | ✓ | Yes |
| B11 | **Floodplain rules differ by jurisdiction.** | "Each jurisdiction follows its own floodplain criteria" (MAAPnext, B2 URL) | ✓ | No: governance issue |
| B-new1 | **Coastal storm surge and evacuation zone confusion** (cycle 20). People near Galveston Bay do not know their evacuation zone or surge depth. Zone data comes from Harris County GIS and surge depth from NHC. | Sources: https://services.arcgis.com/su8ic9KbA7PYVxPS/arcgis/rest/services/HurricaneEvac_Zones/FeatureServer/0 and https://mapservices.weather.noaa.gov/tropical/rest/services/tropical/StormSurgeRisk/MapServer. No numbers are claimed. | (c20, not re-fetched) | Yes |

## C. No insurance, and rising prices (7)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| C1 | **Low coverage.** Most flooded homes had no flood insurance, so owners absorbed the loss. | "only 36 percent of the homes that flooded in the county were covered by flood insurance" (Community Impact, A9 URL) | ✓ | Yes |
| C2 | **Most at-risk homes are uninsured.** | Researcher quote: "92% of at-risk homes do not have flood insurance coverage" (Click2Houston, B7 URL). It is a spoken quote, not a published statistic. Rice's release says "the vast majority" (Rice, B3 URL). Rice also says: "Regardless of what the latest FEMA maps say, get flood insurance." | ✓ (as a quote) | Yes |
| C3 | **The 30-day wait.** Coverage starts 30 days after purchase, so buying once a storm is forecast is too late. | "Your flood insurance coverage will go into effect 30 days after your date of purchase" (FloodSmart: https://www.floodsmart.gov/get-insured/buy-a-policy). **[CORRECTED]** Exceptions: no wait when buying with a mortgage that is made, increased, extended or renewed; no wait when changing coverage at renewal; a 1-day wait for a newly designated high-risk zone (bought within 12 months); a 1-day wait after federal-land wildfire flooding. | ✓* | Yes: countdown tool (with exceptions line) |
| C4 | **Premiums rise under Risk Rating 2.0.** | "91% (268,490)" of Harris County single-family policyholders face increases; full-risk premium $1,200-$2,975 vs. a 2021 average of $541 (CSFI white paper: https://uphelp.org/wp-content/uploads/2024/11/CSFI-White-Paper-An-Evaluation-of-Risk-Rating-2.0-Impacts-on-National-Flood-Insurance-Program-Affordability.pdf) | ? PDF unreadable today. Do not present as verified. | Partly: shows local premium samples |
| C5 | **No affordability help.** | The CSFI paper says there is no NFIP affordability program and that 51% of uninsured households in high-risk zones are low-income. | ? same PDF | No: federal policy |
| C6 | **Price changes are not disclosed in advance.** | The CSFI paper says increases were "without disclosure of NFIP price trajectories". | ? same PDF | Partly |
| C7 | **People underestimate risk.** | FEMA counts about 9M properties at substantial risk vs. First Street's 14.5M (CNBC, secondary: https://www.cnbc.com/2020/08/26/every-us-home-gets-flood-risk-score-and-many-are-at-higher-risk.html) | ? HTTP 403 today | Yes: concrete address-level facts |

## D. Warnings do not reach people in time (7)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| D1 | **The county gage map is not a warning system.** It shows gauges, not street flooding or depth, and lags. | Per the earlier read: "not intended as a notification system", "does not show all flooding", "does not include water depth", up to a 15-minute lag (Harris County FWS: https://harriscountyfws.org/Help) | ? page is too large; the tool read only the first 100k characters and found none of the phrases | Yes |
| D2 | **Signing up for alerts takes effort.** | "You will not receive ALERTS! until the account is validated" (FWS Help, same URL) | ? same | Yes |
| D3 | **Alerts are by county or zone, not street.** | NWS API docs support filtering by state and by county/zone UGC; the point filter is not on that page (NWS: https://www.weather.gov/documentation/services-web-api). A User-Agent is required. | ✓ (partly) | Yes: address-level alerting |
| D4 | **Flash floods leave little time.** | Rainfall of "Nearly 11 inches in 3 hours" and "8-10 inches in three hours" (HCFCD timeline: https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf; Rice, B3 URL) | ? timeline PDF unreadable; Rice not re-checked for this quote | Yes |
| D5 | **Language and accessibility gaps.** | Harris County has "the 5th largest population of persons with different types of disabilities". The accessible alert system offers sign-language interpreting, voice and closed captioning in English and Spanish, and Braille-reader capability (ReadyHarris: https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system). **[CORRECTED]** The release does not say "ASL" literally. Limited-English gap: the 2009 City health inquiry found Chinese, Somali, Spanish and Vietnamese speakers poorly informed, and Beryl resources were mostly English/Spanish only (c1: https://apha.confex.com/apha/138am/webprogram/Paper230593.html). | ✓* | Yes: multilingual UI and voice |
| D6 | **The live roadway flood feed is not public.** | "to inquire about gaining access to the live data feeds, please contact" Houston TranStar (https://traffic.houstontranstar.org/api/api_doc.aspx). DriveTexas returned HTTP 500 on 11 Oct (c28). | ✓ | No: agency decision |
| D7 | **Data sources are changing.** | "WaterServices will be decommissioned in the first quarter of 2027" (USGS: https://waterdata.usgs.gov/blog/api-waterservices-decom/). A later cycle note says Feb 22 2027 (docs/sources.md). | ✓ (quarter) | No: a build risk, not a resident harm |

## E. Vulnerable people (5, plus 4 new)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| E1 | **Older and disabled residents are at higher risk.** | In Harvey, people over 50 (56%) and males (70%) were overrepresented; 29% were over 65 (NHESS, A5 URL). Harris County has "the 2nd largest population of older adults with disabilities in the United States" (ReadyHarris, D5 URL). | ✓ | Yes: profile-based plan |
| E2 | **People who depend on medical care die when cut off.** | "Electrocution and lack of medical treatment each caused four fatalities" (NHESS) | ✓ | Yes: dialysis and clinic routing |
| E3 | **Buyout displaces renters.** Tenants are not the landowners who receive offers and may have nowhere to go. | HCD page: 114 properties planned for demolition; "28 properties of those 34 properties classify as affordable and must be replaced" (https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/Involuntary-Buyout-Relocation-Program). **[CORRECTED]** 72 of the 114 are substantially damaged (no replacement required) and 8 are undetermined, so "only 28 of 114" overstates it. The KSAT "nowhere to go" quote was from a woman living in a tent on land owned by someone else, not a tenant (KSAT: https://www.ksat.com/news/texas/2024/05/20/the-government-wants-to-buy-their-flood-prone-homes-but-these-texans-arent-moving/). Displaced tenants may be entitled to relocation help under the federal Uniform Relocation Act (49 CFR Part 24) if the acquisition is federally funded (c28: https://www.ecfr.gov/current/title-49/subtitle-A/part-24). | ✓* | Partly: rights card; the buyout design is policy |
| E4 | **Repeat flooding causes lasting harm.** | A Meyerland home "flooded three times" (Memorial Day, Tax Day, Harvey) (Click2Houston, B7 URL). KSAT: "twice in seven years". Harris County **excluding Houston** has 869 Severe Repetitive Loss properties and $400,054,157 in NFIP paid losses over 5,364 claims (HCD, E3 URL). **[CORRECTED]** The "largest of any US area" claim is not confirmed. | ✓* | Partly: buyout pointers and history |
| E5 | **Critical services shut down.** | Imelda: Riceland Medical Center (Chambers County) evacuated (Wikipedia, A9 URL). June 2026: flooding closed UH-Downtown, including its food bank (Click2Houston, A7 URL). Allison "TMC shut down" and the IAH closure were not re-checked. | ✓ (partly) | Partly: status links (airport status API tested in c28) |
| E-new1 | **Power-dependent residents** (c27). People on oxygen, ventilators or dialysis face outages after floods. Generator carbon monoxide is the usual killer afterwards. | Harris County has 28,811 Medicare beneficiaries on power-dependent devices (HHS emPOWER, tested c27: https://catalog.data.gov/dataset/hhs_empower_rest_service_public; not re-fetched). CDC: use generators "outside, more than 20 feet away from any windows, doors, and vents" and a battery CO alarm (https://www.cdc.gov/carbon-monoxide/about/index.html). Texas STEAR does not guarantee help ("Registering for STEAR doesn't guarantee you assistance in an emergency", https://tdem.texas.gov/stear). Utility critical-care status does not promise faster restoration (KHOU, c27, not re-fetched). | ✓ (CDC, STEAR) / (c27) | Partly: checklist and numbers; cannot supply power |
| E-new2 | **Manufactured-home residents** (c27). Mobile homes are the least safe shelter in a flood or wind. | FEMA advises occupants of manufactured housing to evacuate when told and move to higher ground (https://www.fema.gov/print/pdf/node/695591; wording is for FEMA temporary units). Do not cite the Ready.gov "Category 5" line (c27). | (c27, not re-fetched) | Partly: text guidance only |
| E-new3 | **Unhoused people near bayous** (c1, c27). Encampments sit in low ground. Harris County adopted "Homelessness on the Bayou" (May 2025): at least 14 days of outreach before closing flood-zone encampments. | https://communityimpact.com/bay-area/government/strategic-and-compassionate-harris-county-adopts-policy-to-address-flood-zone-homeless-encampments/ (c1). 211 Texas lists shelter help: https://www.211texas.org/ | (c1, not re-fetched) | Partly: 211 handoff only; no consumer fit |
| E-new4 | **Households without a car** (c1). They cannot self-evacuate. | Only weak figures exist: about 7% of Greater Houston households have no gas car (UH Space City panel: https://www.uh.edu/hobby/research/space-city-panel/csv-data-folder/space_built_environment.pdf). Do not cite as a statistic; the ACS table is needed. Census API needs a key (c27). | Not verified | Partly: transit and 211 pointers |

## F. Infrastructure, funding, governance (7)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| F1 | **Aging reservoirs risk failure.** Addicks and Barker dams are old earthen structures. | The Corps' studies since 2004 found a "high risk of failure due to seepage and piping issues"; "more than $100 million in major repairs needed", not all completed (Texas Tribune: https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/). **[CORRECTED]** "Extremely high risk" is not in the article; do not use it. The "2010 document never made public" is lawyer Jim Blackburn's assertion; the document surfaced via a 2011 lawsuit. | ✓* | Partly: live pool level (ADDT2 tested in c28), cannot fix dams |
| F2 | **Reservoir releases flood homes.** | "5,138 of those homes flooded" of about 14,000 homes inside the reservoirs; "At least 4,000 more homes have been built inside the reservoirs since Allison" (ProPublica/Tribune: https://projects.propublica.org/graphics/harvey-reservoirs) | ✓ | Partly: reservoir-area check |
| F3 | **Development paves over absorbing land.** | "In the decade after Tropical Storm Allison, about 167,000 acres were developed in Harris County" (ProPublica: https://projects.propublica.org/graphics/harvey). **[CORRECTED]** Cycle 27 correctly removed this figure from the reservoir knowledge card because it is not on the /graphics/harvey-reservoirs page. It does appear verbatim on /graphics/harvey, so cite only that URL, for "Harris County". Do not attribute it to the reservoirs page. | ✓ | Partly: new-construction checklist |
| F4 | **The 2018 flood bond is behind schedule.** | Auditor memo (June 2025): 43 of 181 projects complete, $864M of $2.5B spent (https://auditor.harriscountytx.gov/portals/auditor/documents/AuditDocs/062725Memo%20-%202018%20Bond%20Program%206.23.2025.pdf). Fox 26 confirms 43 of 181 (c27). **[CORRECTED]** The 181 are "bond IDs", so say "43 of 181 bond project groups". Sept 18 2025: commissioners approved a restructuring; $4.16B remains for 147 projects (county release: https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond). | ? memo PDF unreadable; ✓ restructure | No: funding and governance |
| F5 | **Partner funding fell through.** | "Out of $834 million FRT funds originally anticipated, only $165 million materialized" (auditor memo, F4 URL) | ? PDF unreadable. The county release page does not mention a shortfall. | No |
| F6 | **Spending does not follow priority scores.** | Funds given "as-needed", not "in order of prioritization scores"; 2nd-quartile $317.5M vs. 1st-quartile $187.3M (auditor memo) | ? PDF unreadable | No |
| F7 | **Governance is fragmented.** | Rice professor Phil Bedient: "The city doesn't talk to the county" (ProPublica, F2 URL) | ✓ | No |

## G. Recovery and rescue (6, plus 6 new)

| ID | Problem and definition | Key evidence (source) | Verified | App? |
|---|---|---|---|---|
| G1 | **Buyouts are slow and poorly known.** | "In some cases, it can take 18 months or longer to approve a buyout application"; "Who do I call?" (KSAT, E3 URL) | ✓ | Partly: eligibility pointers, not speed |
| G2 | **Rescue demand overwhelms responders.** | "more than 120 000 people were rescued" in Harvey (NHESS). Rosenberg PD: "A downed tree even fell [on] one of our high water rescue vehicles" (Beryl; MPR: https://www.mprnews.org/story/2024/07/08/npr-hurricane-beryl-texas). The "6 volunteers drowned" detail was not re-checked. | ✓ (partly) | Partly: citizens can avoid needing rescue |
| G3 | **Hazards after the flood.** | Electrocution killed four in Harvey (NHESS). Imelda: one electrocution, in a footnote and in Beaumont, not Houston (Wikipedia, A9 URL). | ✓ | Yes: checklists |
| G4 | **Aid arrives slowly.** | "Within the weeks following Imelda, aid from FEMA was not received" (Wikipedia, secondary, A9 URL) | ✓ (secondary) | No: federal process; app can only guide applications |
| G5 | **Flood-death data is fragmented.** | Death reporting "varied greatly between counties", and Harris was the only county with a public casualty list (NHESS). Not re-checked today. | (c, not re-checked) | Partly |
| G6 | **Storms come back to back.** | HCFCD timeline (1929, 1989 events; "every two years") (https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf); MAAPnext | ? PDF unreadable | Partly: reminders and season calendar |
| G-new1 | **Post-flood mold** (c1, c33). Cost barriers lead to long mold exposure and unsafe cleanup. | Houston-3H (347 residents): mold exposure linked to allergic symptoms for up to a year (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9198619/, c1). EPA: about 10 sq ft or less can usually be handled yourself; porous items "may have to be thrown away" (https://www.epa.gov/mold/mold-cleanup-your-home). | ✓ (EPA) / (c1) | Yes: cleanup checklist |
| G-new2 | **Flood-damaged cars resold** (c1). Titles are sometimes altered or washed through other states. | Cox estimate of up to about 500,000 Harvey cars; NICB VINCheck (Fox News, secondary: https://www.foxnews.com/us/after-hurricane-harvey-what-will-happen-to-the-hundreds-of-thousands-of-flooded-cars) | (c1, not re-fetched) | Yes: VIN-check pointer |
| G-new3 | **Post-flood scams and price gouging** (c1, c33). | Texas AG warns about upfront-payment contractors; price gouging is barred after a governor's declaration; report line (800) 621-0508 (https://www.texasattorneygeneral.gov/news/releases/attorney-general-paxton-warns-disaster-scams-following-texas-floods) | (c1, not re-fetched; one AG page returned HTTP 402 in c33) | Yes |
| G-new4 | **FEMA denials and appeals** (c1). Many applicants are ruled ineligible and give up. | Harvey, Texas: of 895,342 registrants, 41% approved and 31% ineligible (Chronicle data via GovTech: https://govtech.com/em/disaster/-disaster-victim-actvists-concerned-about-femas-fairness-transparency.html). Appeal deadline: confirm the current window on fema.gov. | (c1, not re-fetched) | Partly: appeal guidance |
| G-new5 | **Floodwater contamination** (c1). Sewage and E. coli in floodwater. | Texas A&M found E. coli at 125 times the swim-safe level in Harvey (CBS: https://www.cbsnews.com/news/harvey-floodwaters-mix-a-foul-brew-of-sewage-chemicals/) | (c1, not re-fetched) | Yes: safety checklist |
| G-new6 | **NFIP claim deadlines and aid options** (c33). Claimants miss the proof-of-loss deadline. SBA loans are poorly known. | FEMA: submit Proof of Loss "within 60 days after the date of loss" (https://www.fema.gov/fact-sheet/submit-flood-insurance-proof-loss-form-within-60-days-loss; page last updated March 2021, so confirm with FloodSmart or NFIP 877-336-2627). SBA: up to $500,000 for a primary residence, up to $100,000 for personal property (https://www.sba.gov/funding-programs/disaster-assistance/physical-damage-loans). | ✓ | Yes: checklist and clock |

---

## Event history used (from research-brief.md)

| Event | Figure | Source | Check |
|---|---|---|---|
| Harvey | 154,170 Harris County homes flooded | Community Impact (A9 URL) | ✓ |
| Imelda | about 8,200 homes (four counties) | Wikipedia (A9 URL) | ✓. Deaths: infobox 7, text 5. "1,700 rescues" is not on the page; it says "more than 1,000 rescued" in Houston and 422 high-water rescues in Harris County. |
| Beryl | ~2.2M customers out, 7+ TX deaths | MPR | ✗ for that page (as of Jul 8 it says "more than 2.6 million" and "At least two deaths") |
| Beryl heat | Half of Harris County Beryl deaths were heat-related | Texas Tribune: https://www.texastribune.org/2024/07/22/texas-hurricane-beryl-heat-deaths/ | ✓. "2.7M customers" is ✗: the article says "nearly 3 million homes and businesses". |
| Jun 15 2026 | Governor disaster declaration for Harris County | Click2Houston (A7 URL) | ✓ |
| Allison, Memorial Day, Tax Day counts | >70,000; >6,000; ~9,820 | HCFCD timeline PDF | ? unreadable |

## Corrections applied (summary)

1. **F1:** dropped "extremely high risk"; only "a high risk of failure due to seepage and piping" is supported.
2. **F3:** the 167,000-acre figure is removed from reservoir copy, because it is not on the reservoirs page. It remains valid only when attributed to https://projects.propublica.org/graphics/harvey, for Harris County.
3. **B9:** the disclosure claim is time-qualified. Texas Prop. Code 92.0135 (landlord notice, 2022) and SB 339 (2019, seller disclosure) now exist.
4. **C3:** the 30-day wait has four exceptions.
5. **F4:** "43 of 181" counts bond groups, not projects. The 2025 restructure is $4.16B for 147 projects.
6. **B5:** the timeline is "possibly 2028"; drop "cannot be used for insurance".
7. **B8:** the "inadequate storm drainage" quote is not on the cited page.
8. **A8:** 81% is drownings overall.
9. **A9:** the ">1,000 caught" Imelda figure is I-10 east of Houston.
10. **E3:** the "nowhere to go" quote is not from a tenant; the 28-of-114 figure needs its context.
11. **Beryl:** the 2.2M/2.7M/7+ figures do not match the cited pages.

## Source index (by publisher; ✓ = verified today, ? = unreadable, (c) = not re-fetched)

**Federal government**
- FEMA/FloodSmart: https://www.floodsmart.gov/get-insured/buy-a-policy ✓; https://www.fema.gov/fact-sheet/submit-flood-insurance-proof-loss-form-within-60-days-loss ✓; https://www.fema.gov/print/pdf/node/695591 (c)
- CDC: https://www.cdc.gov/carbon-monoxide/about/index.html ✓
- EPA: https://www.epa.gov/mold/mold-cleanup-your-home ✓
- SBA: https://www.sba.gov/funding-programs/disaster-assistance/physical-damage-loans ✓
- NWS: https://www.weather.gov/documentation/services-web-api ✓ (partly)
- USGS: https://waterdata.usgs.gov/blog/api-waterservices-decom/ ✓
- HHS emPOWER: https://catalog.data.gov/dataset/hhs_empower_rest_service_public (c)
- eCFR 49 CFR 24: https://www.ecfr.gov/current/title-49/subtitle-A/part-24 (c)
- NHC / NOAA surge and Harris GIS evacuation zones: see B-new1 (c)

**Texas and Harris County government**
- HCFCD MAAPnext: https://maapnext.harriscountytx.gov/Understand-Your-Risk ✓; https://www.hcfcd.org/MAAPnext (moved, 301 to https://www.maapnext.org/, not followed)
- Harris County Precinct 4 flood bond: https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond ✓ (shortfall not stated)
- Harris County HCD buyouts: https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/Involuntary-Buyout-Relocation-Program ✓
- Harris County Auditor memo: https://auditor.harriscountytx.gov/portals/auditor/documents/AuditDocs/062725Memo%20-%202018%20Bond%20Program%206.23.2025.pdf ?
- HCFCD history timeline: https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf ?
- Harris County FWS: https://harriscountyfws.org/Help ?
- ReadyHarris: https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system ✓
- Houston TranStar: https://traffic.houstontranstar.org/api/api_doc.aspx ✓
- TDEM STEAR: https://tdem.texas.gov/stear ✓
- Texas Legislature SB 339: https://capitol.texas.gov/tlodocs/86R/analysis/pdf/SB00339S.pdf ?
- Texas AG: https://www.texasattorneygeneral.gov/news/releases/attorney-general-paxton-warns-disaster-scams-following-texas-floods (c)
- 211 Texas: https://www.211texas.org/ (c)

**Academic and peer-reviewed**
- TMC dissertation: https://digitalcommons.library.tmc.edu/dissertations/AAI1470211 ✓
- LSU thesis: https://repository.lsu.edu/gradschool_theses/5466 ✓
- NHESS 2018: https://nhess.copernicus.org/articles/18/1073/2018/ ✓
- Rice News: https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk ✓
- Houston-3H mold study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9198619/ (c)
- CSFI white paper: https://uphelp.org/wp-content/uploads/2024/11/CSFI-White-Paper-An-Evaluation-of-Risk-Rating-2.0-Impacts-on-National-Flood-Insurance-Program-Affordability.pdf ?
- UH Hobby School panel: https://www.uh.edu/hobby/research/space-city-panel/csv-data-folder/space_built_environment.pdf (c)
- APHA abstract: https://apha.confex.com/apha/138am/webprogram/Paper230593.html (c)

**Investigative journalism**
- ProPublica/Texas Tribune: https://projects.propublica.org/graphics/harvey-reservoirs ✓; https://projects.propublica.org/graphics/harvey ✓
- Texas Tribune: https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/ ✓; https://www.texastribune.org/2024/07/22/texas-hurricane-beryl-heat-deaths/ ✓

**News (secondary)**
- Community Impact: https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county ✓; https://communityimpact.com/bay-area/government/strategic-and-compassionate-harris-county-adopts-policy-to-address-flood-zone-homeless-encampments/ (c)
- Click2Houston/KPRC: https://www.click2houston.com/news/local/2026/04/21/new-maps-reveal-hidden-flood-danger-across-houston/ ✓; https://www.click2houston.com/news/local/2026/06/16/this-is-not-over-harris-county-braces-for-more-flooding/ ✓; https://www.click2houston.com/news/local/2026/06/15/list-houston-area-intersections-roads-most-likely-to-flood-during-heavy-rain/ (c)
- Observer-Reporter: https://cs.observer-reporter.com/news/2016/apr/21/driver-deaths-spur-investigation/ ✓
- KSAT: https://www.ksat.com/news/texas/2024/05/20/the-government-wants-to-buy-their-flood-prone-homes-but-these-texans-arent-moving/ ✓
- MPR/NPR: https://www.mprnews.org/story/2024/07/08/npr-hurricane-beryl-texas ✓ (partly; see Beryl row)
- ReduceFlooding: https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/ ✓
- CNBC: https://www.cnbc.com/2020/08/26/every-us-home-gets-flood-risk-score-and-many-are-at-higher-risk.html ? (HTTP 403)
- Fox News: https://www.foxnews.com/us/after-hurricane-harvey-what-will-happen-to-the-hundreds-of-thousands-of-flooded-cars (c)
- CBS: https://www.cbsnews.com/news/harvey-floodwaters-mix-a-foul-brew-of-sewage-chemicals/ (c)
- GovTech: https://govtech.com/em/disaster/-disaster-victim-actvists-concerned-about-femas-fairness-transparency.html (c)
- ABC13: https://abc13.com/amp/post/flood-warnings-texas-rental-law-landlords-renters/11399135/ (c)

**Reference**
- Wikipedia (Imelda, secondary): https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019) ✓

## Claims that failed or could not be verified

**Failed (contradicted or absent on the cited page)**
- "Extremely high risk" for the reservoirs (Texas Tribune): absent.
- 167,000 acres on the reservoirs page: absent. It is present on /graphics/harvey.
- "Inadequate or overloaded storm drainage systems" quote (MAAPnext): absent.
- "Cannot be used for insurance or regulatory decisions" (ReduceFlooding): absent. Also, the 30% rainfall increase is not tied to the 2007 maps.
- Imelda "1,700 rescues": not on the Wikipedia page. The ">1,000 vehicles" figure is I-10 Winnie-Orange.
- Beryl "2.2M customers" and "7+ deaths" (MPR): the page says more than 2.6M and at least 2. Beryl "2.7M customers" (Texas Tribune): the page says nearly 3M homes and businesses.
- The "3,600 homes" figure is not in the Rice release (it is in the KPRC article).
- KSAT "nowhere to go" as a tenant: not a tenant.
- "Only 28 of 114 units replaced": incomplete; 72 are substantially damaged and exempt.
- Vehicle share of Harvey drownings: 21 of 57, so "81% in vehicles" is wrong.

**Could not be verified today (unreadable or blocked, not disproven)**
- Auditor memo: $864M, 43/181, $165M of $834M, $317.5M vs $187.3M.
- CSFI paper: 91% (268,490), $1,200-$2,975 vs $541, 51% low-income, "price trajectories".
- HCFCD timeline PDF: Allison, Memorial Day and Tax Day counts; "nearly 11 inches in 3 hours".
- harriscountyfws.org/Help quotes (D1, D2, B8).
- SB 339 text (the PDF is binary; the claim is carried from c27).
- CNBC First Street 14.5M vs FEMA 9M (HTTP 403).
- hcfcd.org/MAAPnext moved to https://www.maapnext.org/ and was not followed.
- Not re-checked: the "6 volunteers drowned" detail, the Allison "TMC shut down" line, the "family of 6 in a van" detail, G5 "varied greatly between counties", and all cycle-sourced `-new` evidence (c).
- Unresolved conflicts from `flood-problems.md`: Harvey deaths 68 (NHC) vs 70 (NHESS: "at least 70"); Harris County 36 vs 37 (NHESS says 37 casualties); Imelda deaths 5 vs 7.
