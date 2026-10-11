# Houston Climate Risks — Research Brief (CodeRED Orion)

*Compiled 2026-10-10. Every number below has a source URL. Items marked **[UNVERIFIED]** must not go on a slide as fact. All APIs listed were tested live on 2026-10-10.*

---

## 0. Summary — the three problems at a glance

| | Flooding | Air quality | Extreme heat |
|---|---|---|---|
| **Headline stat** | Harvey flooded 154,170 Harris County homes; only 36% insured | Houston is #6 worst in the US for ozone; 43.3 bad-ozone days/yr (up from 34.8) | 61 heat deaths in Harris County (2023); heat illness up 329% 2019→2023 |
| **Most surprising fact** | ~Half of Harvey-flooded homes were **outside** mapped floodplains | Fifth Ward residents live **16 fewer years** than River Oaks (69 vs 85) | Half of Beryl's Harris County deaths were **heat**, not wind or water |
| **Who's hit hardest** | Drivers (77% of TX flood deaths), renters, underinsured | Fenceline communities (Fifth Ward, Manchester, Galena Park), kids, lower-income | Older adults (39% of heat illness), renters without AC, outdoor workers |
| **What existing tools miss** | Gauge-centric, not address-centric; FEMA maps from 2007; no plain-language "what do I do" | Region-wide, day-ahead ozone alerts; no hourly "bad hours"; alerts only EN/ES | Static cooling-center list (all "Open", weekday hours); rides need a 311 call; no check-ins for isolated elders |
| **Best free API (no key)** | USGS gauges + NWS alerts + FEMA flood zone lookup | Open-Meteo Air Quality (hourly ozone forecast) | NWS gridpoints (`heatRisk` 0–4) + City cooling-center ArcGIS layer |

**Shared app gap (team synthesis, not a cited finding):** no tool combines live data + *your address* + plain-language actions across all three hazards.

**Action item:** request an EPA AirNow API key now (https://docs.airnowapi.org/account/request) — approval may not be instant. Everything else needs no key.

---

## 1. FLOODING

### 1.1 Scale and history
| Event | Key figures | Source |
|---|---|---|
| TS Allison (Jun 2001) | 22 deaths, >70,000 structures flooded, >$5B (HCFCD). FEMA says 23 deaths; Fox 26 says $9B **[CONFLICTING]** | https://www.hcfcd.org/portals/62/about/flooding-history/historytimeline-24x36-1.pdf |
| Memorial Day (May 2015) | >6,000 structures flooded, 7 deaths (HCFCD) | same HCFCD timeline |
| Tax Day (Apr 2016) | 12–16 in. of rain in 12 hrs, ~9,820 structures flooded, 7 deaths; 2015+2016 floods: 16 dead, >$1B | HCFCD; https://projects.propublica.org/graphics/harvey |
| **Harvey (Aug 2017)** | **154,170 Harris County homes flooded; only 36% insured; ~half outside 100/500-yr floodplains**; 36 Harris County deaths. Statewide: 68 direct deaths, ~$125B damage (NHC; 90% range $90–160B), 300,000+ structures | https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county ; https://khou.com/article/news/nhc-harvey-is-second-most-costly-hurricane-in-us-68-deaths-in-texas/285-511430188 |
| Imelda (Sep 2019) | ~8,200 homes flooded across 4 counties; 2 Harris County deaths; ≥1,700 rescues | https://en.wikipedia.org/wiki/Tropical_Storm_Imelda_(2019) |
| Beryl (Jul 2024) | Mostly wind and power: ~2.2M customers out; ≥7 TX deaths. Final NHC totals **[UNVERIFIED]** | https://www.mprnews.org/story/2024/07/08/npr-hurricane-beryl-texas |
| Jun 15, 2026 flash flood | Downtown flooding, cars stranded under bridges, UH-Downtown closed, state disaster declaration | https://www.click2houston.com/news/local/2026/06/16/this-is-not-over-harris-county-braces-for-more-flooding/ |

**Repeat flooding:** Harris County (excluding Houston) has 869 Severe Repetitive Loss properties with $400M in NFIP claims paid — the largest of any US area. https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/Involuntary-Buyout-Relocation-Program

### 1.2 Current state (2025–2026)
- **Rice University re-modeled the Tax Day storm (Apr 2026):** over Clear Creek, ~3,600 homes would flood; shifting the storm center a few miles pushes that to >13,000, many outside official floodplains. Nearly half of the Hunting Bayou watershed could flood. Public dashboard: https://rice1.osn.mghpcc.org/crc-ssl/CFAR_MVP/TaxDayFloodsRevisited/index.html — https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk
- **The "92%" figure is a spoken quote, not a published statistic:** *"92% of at-risk homes do not have flood insurance coverage," said Rice researcher Yilei Yu* (KPRC). Rice's own release says only "the vast majority." If used, present it as a quote. https://www.click2houston.com/news/local/2026/04/21/new-maps-reveal-hidden-flood-danger-across-houston/
- **Insurance uptake:** ~240,000 NFIP policies for ~1.175M housing units (~20 per 100), down from 295,108 policies in 2022. Kinder Institute 2025: <25% of residential structures insured.
- **New FEMA flood maps (MAAPnext):** draft maps released Feb 2026, based on Atlas 14 rainfall rates **>30% higher** than the 2007 maps still in effect. Final maps are expected ~2028–29. https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/
- **2018 flood bond:** restructured Sept 2025 — $4.16B remaining across 147 projects. Much of the expected partner funding never arrived. https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond

### 1.3 Root causes
- Flat, clay-soil terrain — "you don't have to live near a bayou to flood." https://maapnext.harriscountytx.gov/Understand-Your-Risk
- Aging Addicks/Barker reservoirs (1940s), rated "extremely high risk"; Harvey releases flooded homes downstream. https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/
- Development and paved surfaces — widely cited, but no current impervious-cover figure was found **[GAP]**.

### 1.4 Who is most affected
- **Drivers:** 77% of Texas flood deaths (1959–2008) came from driving into water, and Harris County leads the state. https://digitalcommons.library.tmc.edu/dissertations/AAI1470211 ; https://repository.lsu.edu/gradschool_theses/5466. 81% of Harvey deaths were drownings. https://nhess.copernicus.org/articles/18/1073/2018/nhess-18-1073-2018.pdf
- **Renters:** >475,000 Harris County residents live in at-risk multifamily housing (2019). https://planetizen.com/node/103514

### 1.5 Existing tools and their gaps
| Tool | What it does | Gap |
|---|---|---|
| Harris County Flood Warning System | ~350 gauges; rainfall and channel levels | No public API; organized around gauges, not addresses |
| ReadyHarris | Alerts in 5 languages, family plans | General preparedness advice, not street-level |
| TranStar flood warning | ~200–283 roadway sensors **[CONFLICTING]** | Instrumented roads only; no rerouting |
| FEMA flood maps | Flood zones | Effective maps date from 2007; miss street ponding |
| First Street Risk Factor | Property risk score | Static; no real-time component |
| NWS alerts | Watches and warnings | County or zone level, not address level |

### 1.6 Free APIs (no key needed)
1. **USGS gauges:** `https://waterservices.usgs.gov/nwis/iv/?format=json&sites=08074000&parameterCd=00065,00060&siteStatus=all` (Buffalo Bayou; updates every ~15 min). ⚠️ This legacy service shuts down Q1 2027; the replacement is `https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-continuous/items?f=json&monitoring_location_id=USGS-08074000`
2. **NWS (User-Agent header required):** `https://api.weather.gov/alerts/active?point=29.76,-95.37`; forecast: `https://api.weather.gov/gridpoints/HGX/63,95/forecast`
3. **NOAA NWPS river gauges with flood stages:** `https://api.water.noaa.gov/nwps/v1/gauges?bbox.xmin=-95.6&bbox.ymin=29.6&bbox.xmax=-95.2&bbox.ymax=29.9&srid=EPSG_4326`; per-gauge `/nwps/v1/gauges/BBST2` (flood stages: action 17 ft / minor 28 / moderate 29.5 / major 32) and `/stageflow`
4. **FEMA flood zone for a point:** `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?geometry=-95.3698,29.7604&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF&returnGeometry=false&f=json`
5. **Open-Meteo rain:** `https://api.open-meteo.com/v1/forecast?latitude=29.76&longitude=-95.37&hourly=precipitation,precipitation_probability` (non-commercial: 10k calls/day)

### 1.7 Pitch-ready facts
1. Harvey flooded 154,170 Harris County homes — only 36% had flood insurance.
2. Nearly half of those homes were outside the 100- and 500-year floodplains.
3. Rice (2026): a Tax Day-size storm over Clear Creek could flood more than 13,000 homes, many outside official floodplains.
4. FEMA's new draft maps use rainfall rates more than 30% higher than the 2007 maps still in effect.
5. 77% of Texas flood deaths happen in vehicles, and Harris County leads the state.

---

## 2. AIR QUALITY

### 2.1 Scale
- **ALA State of the Air 2026 (covering 2022–24):** Houston is the **6th worst** US metro for ozone, at **43.3 unhealthy-ozone days per year** (grade F), up from 7th and 34.8 days in 2025. It ranks 8th worst for year-round particle pollution. Brazoria, Galveston, Harris and Montgomery counties all got an F for ozone. https://www.lung.org/media/press-releases/fy26-sota-texas ; https://communityimpact.com/tomball-magnolia/healthcare/houston-area-rises-1-spot-now-no-6-most-polluted-city-by-ozone/
- **Federal ozone status (Houston-Galveston-Brazoria):** **Severe** nonattainment of the 2008 standard (deadline Jul 2027) and **Serious** nonattainment of the 2015 standard (deadline Aug 2027). https://www.tceq.texas.gov/airquality/sip/hgb/hgb-status
- **Fine particles (PM2.5):** EPA lowered the annual standard from 12 to **9 µg/m³** in Feb 2024. Harris County's design value is **12.5 µg/m³, the highest in Texas**. A court has ordered EPA to finalize nonattainment designations by Feb 6, 2027. https://www.houstonlanding.org/12-texas-counties-failed-federal-air-quality-standards-only-4-including-harris-will-be-reported-to-epa/ ; https://stylemagazine.com/news/2026/jul/29/harris-county-attorney-abbie-kamin-secures-court-order-requiring-implementation-of-life-saving-soot-standard/

### 2.2 Health impact
- **631 premature deaths from PM2.5 and 159 from NO2** in Houston in 2010, falling hardest on lower-income households. https://pmc.ncbi.nlm.nih.gov/articles/PMC7068272
- A 20 ppb rise in ozone was linked to up to **4.4% higher cardiac-arrest risk** within 1–3 hours (Rice, 11,677 cases). https://news.rice.edu/2013/02/17/rice-university-analysis-links-ozone-levels-cardiac-arrest/
- **Fifth Ward vs. River Oaks:** asthma 11% vs 7%; **life expectancy 69 vs 85**; NO2 48% above the city average; **46% of monitored schools and childcare centers** had above-typical NO2. https://edf.org/airqualitymaps/houston/findings
- Black children were more than twice as likely as white children to have asthma (Rice, 2017). https://abc13.com/post/study-black-kids-at-higher-risk-for-asthma/1815748/
- Manchester's 1,3-butadiene level exceeded EPA's cancer-risk threshold (BEE-TEX study, 2015). https://doaj.org/article/123da6c77d02433cae71cded1036998e
- **[UNVERIFIED]** Current childhood asthma rate; "5,000 deaths" (advocacy material); "800,000 children in chemical danger zones" (advocacy material).

### 2.3 Root causes and incidents
- Petrochemical plumes form ozone efficiently from ethene and propene, and emissions were under-reported. https://pmc.ncbi.nlm.nih.gov/articles/PMC404047
- Traffic dominates ozone at some monitoring sites. https://onebreathhou.org/newsroom/2020/05/ozone-pollution-industrial-emissions-houston/
- Ozone season runs roughly Mar–Nov; ozone peaks on sunny, hot afternoons.
- **Chemical incidents:**
  - ITC Deer Park fire (Mar 2019): benzene up to ~190 ppb, shelter-in-place. https://abc13.com/shelter-in-place-issued-for-deer-park-after-fire-at-itc-plant/5200816/
  - Pemex H2S leak (Oct 2024): 2 dead, 35 treated. https://www.nbcnews.com/news/us-news/2-dead-hydrogen-sulfide-leak-houston-area-pemex-facility-rcna174984
  - Marathon Texas City fire (**Jun 2026**): shelter-in-place. https://abc13.com/post/tceq-report-shows-air-contaminants-released-during-texas-city-plant-fire/19356885/

### 2.4 Existing tools and their gaps
- **TCEQ Ozone Action Days:** region-wide forecasts, about a day ahead — not hyperlocal or hourly. https://www.tceq.texas.gov/airquality/monops/ozone_email.html
- **State data:** hard to interpret and not available in Spanish. https://www.ehn.org/language-justice
- **AlertHouston:** English and Spanish only.
- **Harris County monitoring:** KHOU found the county still couldn't adequately track air quality after 4 plant fires in 5 months. https://www.khou.com/article/news/health/4-plant-fires-in-5-months-report-reveals-harris-co-still-cant-adequately-track-air-quality/285-88111ecc-6899-4436-bf10-dc4f58ef7e7e
- **Air Alliance Houston dashboard:** ~60 low-cost sensors (TCEQ has 47 monitors; Harris County has 12). https://www.northchannelstar.com/2025/07/air-alliance-unveils-updated-air-quality-dashboard/

### 2.5 Free APIs
| API | Auth | Limits | Example |
|---|---|---|---|
| **Open-Meteo Air Quality** | none | 10k/day | `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=29.76&longitude=-95.37&current=us_aqi,pm2_5,ozone&hourly=us_aqi,ozone&timezone=America/Chicago` (~45 km grid; credit CAMS) |
| EPA AirNow | free key | hourly cap | `https://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude=29.76&longitude=-95.37&distance=25&API_KEY=KEY` |
| PurpleAir | key | 1M free points for new users | `GET https://api.purpleair.com/v1/sensors?fields=pm2.5_atm,latitude,longitude&nwlat=29.9&nwlng=-95.6&selat=29.6&selng=-95.1` |
| OpenAQ v3 | key | 60/min | `https://api.openaq.org/v3/locations?coordinates=29.76,-95.37&radius=10000` |

### 2.6 Pitch-ready facts
1. Houston is the 6th worst US metro for ozone, with unhealthy days up from 34.8 to 43.3 a year.
2. The region is officially in "severe" violation of the federal ozone standard.
3. Fifth Ward residents live 16 fewer years than River Oaks residents and breathe 48% more NO2.
4. 46% of Houston schools and childcare centers that EDF monitored had above-typical NO2.
5. Fine-particle pollution was linked to an estimated 631 premature deaths in Houston in one year.

---

## 3. EXTREME HEAT

### 3.1 Scale
- **Harris County: 61 heat deaths in 2023**, likely undercounted. Texas recorded 334–563 heat deaths that year, depending on the count method. https://abc13.com/post/despite-record-heat-related-deaths-experts-say-theres-more/15178603/ ; https://www.texastribune.org/2024/01/12/texas-heat-deaths-2023-record-climate-change/
- Texas 2024 (preliminary): heat killed 171 people and contributed to 281 more deaths. https://insideclimatenews.org/news/17082025/el-paso-extreme-heat-illness-death/
- **Heat illness in Harris County rose 329% from 2019 to 2023; older adults made up 39%.** https://abc13.com/post/houstons-excessive-heat-rise-emergency-room-related-visits-harris-county-public-health-study-shows/15668741/
- 1,630 heat-illness ER visits from Apr 1 to Aug 7, 2025 (Harris, Fort Bend and Montgomery counties). https://localnews8.com/news/2025/08/12/houston-health-department-unveils-groundbreaking-dashboard-to-combat-extreme-heats-toll-on-health/
- **Summer 2023, the hottest on record:** 45 days at or above 100°F; hit 109°F twice. https://abc13.com/texas-weather-2023-events-top-moments-in-southeast-record-heat/14227015/
- Nights aren't cooling — dozens of record-high overnight lows in 2020. Extreme Heat Warning on Jul 22, 2026, with heat index up to ~115°F.
- **[UNVERIFIED]** Harris County heat-death totals for 2024, 2025 and 2026.

### 3.2 Power outages + heat
- **Beryl (Jul 2024):** ~2.7M Texas customers lost power; **half of Harris County's storm deaths were heat-related**; ≥22 Houston-area deaths, more than half tied to the outages. https://www.texastribune.org/2024/07/22/texas-hurricane-beryl-heat-deaths/ ; https://www.houstonpublicmedia.org/articles/news/hurricane/2024/07/18/494068/hurricane-beryl-deaths-houston-at-least-20-half-power-outage-related/
- **Derecho (May 2024):** >900,000 customers lost power; ~8 deaths.
- Pitch angle: Houston's deadliest heat events came from local power outages, not statewide grid shortfalls.

### 3.3 Urban heat island
- **2020 heat mapping:** at the same moment, Richmond Ave was 103.3°F and Channelview 86.2°F — a **17°F spread**. Alief and Gulfton were among the hottest areas. https://www.click2houston.com/news/local/2021/01/06/some-houston-area-neighborhoods-are-hotter-than-others-report-says-heres-why-thats-possible/
- **Tree canopy:** Gulfton ~4–6% vs. West University Place 38%, five miles away. https://sierraclub.org/texas/houston/blog/2023/08/urban-heat-island-strategies-and-projects

### 3.4 Who is most affected
- **Older adults** (39% of heat illness; Beryl victims were found at home).
- **Renters:** Texas has no statewide requirement for landlords to provide AC. **NEW: Houston City Council passed a "Right to Air Conditioning" rental ordinance on Aug 19, 2026** (effective date unclear). https://www.click2houston.com/news/local/2026/08/19/houston-council-members-passes-ordinance-requiring-working-ac-in-rental-properties/
- **Outdoor workers:** the "Death Star" law (HB 2127) blocks city water-break rules; it was upheld on appeal in Jul 2025. https://www.texastribune.org/2025/07/18/texas-legislature-death-star-law-city-ordinances-limits/
- **Unhoused people:** 3,321 counted in 2026. https://www.cfthhouston.org/extreme-heat-resources-summer-2026

### 3.5 Existing tools and their gaps
| Tool | Gap |
|---|---|
| City cooling-center map (houstonoem.org/extreme-heat) | Static: every site shows "Open" with fixed weekday hours; extended hours appear only in the news; free rides require calling 311 or METROLift |
| 112 centers opened in Jul 2026 | No live status or capacity |
| NWS/CDC HeatRisk | 0–4 scale by ZIP code; no outreach and no personalized actions |
| OSHA-NIOSH heat app | "Not receiving updates" |
| **Missing everywhere** | Proactive check-ins with isolated elders; live center status; one-tap rides; personal risk (age, AC, medications, job, power loss); a power-outage mode |

### 3.6 Free APIs (no key needed)
1. **NWS gridpoints:** `https://api.weather.gov/gridpoints/HGX/63,95` includes `heatIndex`, `apparentTemperature`, `wetBulbGlobeTemperature` and **`heatRisk` (0–4)**, in °C.
   - Alerts: `https://api.weather.gov/alerts/active?zone=TXZ213&event=Extreme%20Heat%20Warning,Heat%20Advisory`
   - ⚠️ NWS renamed "Excessive Heat" to "Extreme Heat" in Mar 2025, so filter on the new name.
2. **NWS HeatRisk image service** (experimental): `https://mapservices.weather.noaa.gov/experimental/rest/services/NWS_HeatRisk/ImageServer/identify?geometry={"x":-95.37,"y":29.76,"spatialReference":{"wkid":4326}}&geometryType=esriGeometryPoint&f=json`
3. **Open-Meteo:** `https://api.open-meteo.com/v1/forecast?latitude=29.76&longitude=-95.37&hourly=temperature_2m,apparent_temperature,relative_humidity_2m&daily=apparent_temperature_max&temperature_unit=fahrenheit&timezone=America%2FChicago`
4. **City of Houston cooling centers (ArcGIS, 135 sites):** `https://services3.arcgis.com/aDc3tOL5l9SNklhS/arcgis/rest/services/COH_MassCare_Public/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson` — fields include name, phone, address and daily hours. Hours are free text, and Status always reads "Open".

### 3.7 Pitch-ready facts
1. 61 people died of heat in Harris County in 2023, and experts say that's an undercount.
2. Heat illness in Harris County rose 329% from 2019 to 2023; older adults made up 39%.
3. Half of Beryl's Harris County deaths were from heat, after ~2.7M Texas customers lost power.
4. Summer 2023: 45 days at or above 100°F, with two days at 109°F.
5. Parts of Houston were 17°F hotter than others at the same moment.
6. Houston opened 112 cooling centers in Jul 2026, but getting a free ride still means calling 311.

---

## 4. Not verified (do not present as fact)
- **Flooding:** final Beryl totals from NHC; 2025–26 flood death counts; how many properties MAAPnext adds to the floodplain; current impervious-cover share; renter NFIP uptake; TranStar sensor count.
- **Air:** current childhood asthma rate; ER visits on high-ozone days; the "5,000 deaths" and "800,000 children" advocacy figures; whether TCEQ offers a public API.
- **Heat:** Harris County heat deaths for 2024–2026; the effective date of the AC ordinance; heat deaths among unhoused people; ReadyHarris heat features.
