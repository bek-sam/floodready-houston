# Houston Flooding: Every Problem Found in the Sources

*Compiled 2026-10-10. About 30 sources were read in full. Four could not be opened (KHOU, Planetizen, the TxDOT PDF, and the Community Impact flipbook), and none of their content is used here.*
*Quotes from PDFs and FloodSmart are verbatim. Quotes from HTML pages were extracted with a summarizing tool and look exact, but were not checked character by character.*

**Solo-buildable** rates whether one person (with Claude) could build a credible app for the problem in about 19 hours: ✅ yes, 🟡 partly, ❌ no (needs policy, infrastructure, or money).

---

## A. Drivers die in flooded roads and underpasses

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| A1 | Most flood deaths happen to people driving into water | "most fatalities result from driving into flood water (77%)" (study period: Texas, 1959–2008); Texas had 840 flood deaths 1959–2009, three times the next state | TMC dissertation: https://digitalcommons.library.tmc.edu/dissertations/AAI1470211 | ✅ |
| A2 | Harris County has the most vehicle flood deaths in Texas, far more than Dallas even though Dallas floods more often | Dallas had "almost seven times less" vehicle-related deaths | LSU thesis: https://repository.lsu.edu/gradschool_theses/5466 | ✅ |
| A3 | The "Turn Around Don't Drown" slogan shows no measurable effect | "no convincing evidence" it reduced deaths; no significant trend since 1996 | LSU thesis (same) | ✅ (generic messaging fails, so personal and timely warnings are the opening) |
| A4 | The same underpasses keep killing people | 3 drivers died at the same underpass in April 2016, after earlier drownings there "last May" | https://cs.observer-reporter.com/news/2016/apr/21/driver-deaths-spur-investigation/ | ✅ |
| A5 | Low-water crossings are not mapped or communicated to the public | The Harvey study authors say high-hazard spots "have not been adequately delineated or communicated to the public" and recommend "preventive closure" | NHESS 2018: https://nhess.copernicus.org/articles/18/1073/2018/nhess-18-1073-2018.pdf | ✅ |
| A6 | Physical warnings are incomplete | Only 19 of 27 sensor and flashing-light sites were installed; barricades on one side only; wooden gates abandoned; Judge Emmett: "not enough has been done"; deaths were "completely preventable" | Observer-Reporter (same) | 🟡 |
| A7 | Drivers go around barricades, so warnings need to reach them before they reach the water | Drivers went around the gate and crashed into it; in June 2026, "vehicles became stuck under bridges" | Observer-Reporter; https://www.click2houston.com/news/local/2026/06/16/this-is-not-over-harris-county-braces-for-more-flooding/ | ✅ |
| A8 | Harvey drownings happened in and around vehicles | 81% of 70 deaths were drownings, "particularly in and around vehicles"; a family of 6 died when their van "was swept off a flooded road" | NHESS 2018 | ✅ |
| A9 | Huge vehicle losses | More than 300,000 vehicles flooded in Harvey; more than 1,000 caught in water and more than 1,600 towed in Houston during Imelda | https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county ; https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019) | ✅ |

**Data available for building:**
- A TranStar roadway-flood JSON sample (`https://traffic.houstontranstar.org/api/roadwayfloodwarning_sample.json`) with sensor location, top of bank, stream elevation and alert flags. The live feed requires asking TranStar for access.
- KPRC's June 2026 list of flood-prone intersections: https://www.click2houston.com/news/local/2026/06/15/list-houston-area-intersections-roads-most-likely-to-flood-during-heavy-rain/
- There is no official open dataset of underpasses.

---

## B. Official maps give people a false sense of safety

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| B1 | Most flooding happens outside FEMA flood zones | "A little less than half" of Harvey-flooded homes were outside both the 100- and 500-year floodplains; "the majority of fatalities were recovered outside the designated 100- and 500-year flood hazard areas" (only 22% of Harris County deaths were inside the 100-year zone) | Community Impact; NHESS | ✅ |
| B2 | Low-risk zones still file many claims | "More than 25% of all flood insurance claims come from properties located in moderate- or low-risk areas" | https://maapnext.harriscountytx.gov/Understand-Your-Risk | ✅ |
| B3 | "Not in a flood zone" misleads people | "'not in a flood zone' is a dangerous misnomer"; "The lines on a FEMA map are often actuarial, not physical" | https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk | ✅ |
| B4 | The maps in force are outdated | Effective maps from 2007 are based on old rainfall data; new Atlas 14 rainfall rates are "more than 30%" higher; maps are "looking in the rearview mirror" | https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/ ; Rice | ✅ |
| B5 | The new maps are years away | The drafts are "not final, not regulatory," "cannot be used for insurance or regulatory decisions," and "not open for formal comments or appeals"; effective in about 2–3 years | ReduceFlooding; https://www.hcfcd.org/MAAPnext | 🟡 |
| B6 | The draft map viewer is hard to use | It "doesn't work on cell phones," zones appear as "shades and dots, not colors," it is "visually confusing," and boundaries are "just a foot or two wide" | ReduceFlooding | ✅ (strong UX opening) |
| B7 | Risk depends on where the storm tracks | Shifting a Tax Day storm a few miles changes flooded homes from about 3,600 to "more than 13,000" | https://www.click2houston.com/news/local/2026/04/21/new-maps-reveal-hidden-flood-danger-across-houston/ | ✅ (simulation) |
| B8 | Flooding from drains and sheet flow away from bayous | Flooding comes from "inadequate or overloaded storm drainage systems, including roadside ditches"; sheet flow can flood "residences that are not even near a creek or bayou" | MAAPnext; https://harriscountyfws.org/Help | 🟡 (hard to model) |
| B9 | No disclosure to buyers and renters | Renter: "When I started to rent this house, nobody told me"; "Even the insurance company told me that it was not a flooding area"; neither the city nor the county requires disclosure; the only warning is a plat note ("Nobody looks at a plat") | https://projects.propublica.org/graphics/harvey-reservoirs | ✅ |
| B10 | People are caught unaware | In June 2026 a UH-Downtown student "had no idea there was a flood" | Click2Houston June 2026 | ✅ |
| B11 | Floodplain rules differ by jurisdiction | "Each jurisdiction follows its own floodplain criteria" | MAAPnext | ❌ |

---

## C. Most people have no flood insurance, and it is getting more expensive

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| C1 | Low coverage | "only 36 percent of the homes that flooded… were covered by flood insurance" (Harvey) | Community Impact | ✅ |
| C2 | Most at-risk homes are uninsured | "92% of at-risk homes do not have flood insurance coverage" (a spoken quote from a Rice researcher; cite it as a quote); Rice's release says "the vast majority would likely not have flood insurance" | Click2Houston April 2026; Rice | ✅ |
| C3 | Coverage starts 30 days after purchase, too late once a storm is coming | "Your flood insurance coverage will go into effect 30 days after your date of purchase" | https://www.floodsmart.gov/get-insured/buy-a-policy | ✅ |
| C4 | Premiums are rising under FEMA's new pricing system (Risk Rating 2.0) | "91% (268,490)" of Harris County single-family policyholders face increases; the full-risk premium is $1,200–$2,975 vs. a 2021 average of $541 | CSFI white paper (2022): https://uphelp.org/wp-content/uploads/2024/11/CSFI-White-Paper-An-Evaluation-of-Risk-Rating-2.0-Impacts-on-National-Flood-Insurance-Program-Affordability.pdf | 🟡 |
| C5 | No affordability help, so coverage drops | "The flood insurance gap is rapidly expanding"; there is no "NFIP affordability program"; 51% of uninsured households in high-risk zones are low-income | CSFI | ❌ (policy) |
| C6 | Price increases are not disclosed in advance | Implemented "without disclosure of NFIP price trajectories" | CSFI | 🟡 |
| C7 | People underestimate risk | Consumers underestimate "the probability and severity of future disasters"; FEMA counts about 9M properties at substantial risk vs. First Street's 14.5M | CSFI; https://www.cnbc.com/2020/08/26/every-us-home-gets-flood-risk-score-and-many-are-at-higher-risk.html | ✅ |

---

## D. Warning systems do not reach people in time

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| D1 | The county gage map is not a warning system | It "is not intended as a notification system"; "does not show all flooding"; misses street ponding and ungaged channels; "does not include water depth"; lags up to 15 minutes | https://harriscountyfws.org/Help | ✅ |
| D2 | Signing up for alerts takes effort | "You will not receive ALERTS! until the account is validated" | FWS Help | ✅ |
| D3 | Alerts are by county or zone, not by street or route | NWS alerts are filtered by area, county or zone and have no road-level endpoint | https://www.weather.gov/documentation/services-web-api | ✅ |
| D4 | Flash floods leave little time | Short storms "don't give the city days to mobilize"; rainfall rates of "8-10 inches in three hours" and "Nearly 11 inches in 3 hours" | Rice; https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf | ✅ |
| D5 | Language and accessibility gaps | Harris County has the "5th largest" population of people with disabilities in the US; accessible alerts (ASL, voice, Braille) exist only in English and Spanish | https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-launches-accessible-alert-system | ✅ |
| D6 | The live roadway flood feed is not public | "to inquire about gaining access to the live data feeds, please contact Houston TranStar" | https://traffic.houstontranstar.org/api/api_doc.aspx | 🟡 |
| D7 | Data sources are changing | The USGS WaterServices API "will be decommissioned in the first quarter of 2027" | https://waterdata.usgs.gov/blog/api-waterservices-decom/ | (affects the build: use the new API) |

---

## E. Vulnerable people

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| E1 | Older and disabled residents are at higher risk | 56% of Harvey victims were over 50 and 29% over 65; 70% were male; Harris County has the "2nd largest population of older adults with disabilities" | NHESS; ReadyHarris | ✅ |
| E2 | People who depend on medical care die when they cannot reach it | 4 Harvey deaths came from "lack of medical treatment" (dialysis, asthma, heart care) | NHESS | ✅ |
| E3 | Renters are displaced by buyouts and have nowhere to go | A tenant "would have nowhere to go"; for 114 demolitions, only 28 affordable units are to be replaced, in distant ZIP codes | https://www.ksat.com/news/texas/2024/05/20/the-government-wants-to-buy-their-flood-prone-homes-but-these-texans-arent-moving/ ; https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/Involuntary-Buyout-Relocation-Program | 🟡 |
| E4 | Repeat flooding causes lasting harm | A Meyerland home flooded 3 times in under a decade, with residents describing ongoing post-traumatic stress; "twice in seven years"; 869 Severe Repetitive Loss properties with $400M in claims | Click2Houston April 2026; KSAT; HCD | 🟡 |
| E5 | Critical services shut down | Allison: "Texas Medical Center essentially shut down"; Imelda: a hospital evacuated, bus and rail shut down, IAH closed; June 2026: the UH-Downtown food bank closed | HCFCD timeline; Wikipedia Imelda; Click2Houston June 2026 | 🟡 |

---

## F. Infrastructure, funding and governance (policy problems; not solvable by an app)

| # | Problem | Evidence | Source |
|---|---|---|---|
| F1 | Aging reservoirs at risk of failure | "high risk of failure due to seepage and piping"; more than $100M in repairs needed; the 2010 risk document was never made public | https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/ |
| F2 | Reservoir releases flood homes downstream | 5,138 of about 14,000 homes inside the reservoirs flooded; about 4,000 of them were built after Allison; releases flooded "thousands more homes" | ProPublica reservoirs; Texas Tribune |
| F3 | Development keeps paving over land that absorbed water | 167,000 acres were developed in the decade after Allison; developers may "rush to develop floodplain properties" before the new maps | https://projects.propublica.org/graphics/harvey ; ReduceFlooding |
| F4 | The 2018 flood bond is behind schedule | 43 of 181 bond projects were complete by March 2025; $864M of $2.5B spent | Auditor memo: https://auditor.harriscountytx.gov/portals/auditor/documents/AuditDocs/062725Memo%20-%202018%20Bond%20Program%206.23.2025.pdf |
| F5 | Partner funding fell through | "Out of $834 million FRT funds originally anticipated, only $165 million materialized" | Auditor memo |
| F6 | Spending does not follow priority scores | Funds were given "as-needed," not "in order of prioritization scores"; 2nd-quartile projects got $317.5M vs. $187.3M for the 1st quartile | Auditor memo; https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond |
| F7 | Governance is fragmented | "The city doesn't talk to the county… Nobody's in charge" | ProPublica reservoirs |

---

## G. Recovery and rescue

| # | Problem | Evidence | Source | Solo-buildable |
|---|---|---|---|---|
| G1 | Buyouts are slow and poorly known | "18 months or longer to approve a buyout application"; "Who do I call?"; offers may not cover a move | KSAT | 🟡 |
| G2 | Rescue demand is overwhelming | More than 120,000 rescued in Harvey; 6 volunteers drowned when their boat capsized; a tree fell on a high-water rescue vehicle during Beryl | NHESS; https://www.mprnews.org/story/2024/07/08/npr-hurricane-beryl-texas | 🟡 |
| G3 | Hazards after the flood | Electrocution (4 Harvey deaths; one in Imelda), infection | NHESS; Wikipedia Imelda | ✅ |
| G4 | Aid arrives slowly | After Imelda, "aid from FEMA was not received" for weeks | Wikipedia Imelda | ❌ |
| G5 | Flood-death data is fragmented | Reporting "varied greatly between counties"; Harris was the only county with a public casualty list | NHESS | 🟡 |
| G6 | Storms come back to back | "As the area is still reeling from the last storm, another major storm hits" (1929); "two back-to-back presidential disaster declarations" (1989); a major flood "every two years" | HCFCD timeline; MAAPnext | — |

---

## Conflicts to resolve before pitching
- **Share of Harvey-flooded homes outside flood zones:** about 75% (KPRC, likely counting only the 100-year zone) vs. "a little less than half" outside **both** the 100- and 500-year zones (official county figure). **Use the county figure.**
- **Harvey deaths:** 68 direct deaths in Texas (NHC) vs. 70 (NHESS, which includes indirect deaths); Harris County 36 vs. 37.
- **Imelda deaths:** the Wikipedia infobox says 7 and the article text says 5.
