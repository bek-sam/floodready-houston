# Competitive landscape (verified Sun Oct 11 2026)

Method: WebSearch + WebFetch on the date above, about 1 hour before pitch. Several official sites (harriscountyfws.org, readyharris.org) did not give full text to the fetcher, so some cells rely on search snippets (often 2014-2022 vintage). Legend: **V** = verified in a source below; **V(old)** = source is dated, current status unconfirmed; **NF** = not found (absence of evidence, not proof of absence).

## 1. Tool x capability table

| Tool | Address-level risk | Harvey / history at your address | Route check vs flood-prone crossings | Real-time alerts for your place | Languages | Voice/AI assistant with sources | Renter/buyer tools | Recovery / FEMA steps | Offline | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| ReadyHarris app | NF (general prep) | NF | NF (has "evacuation route maps" [1]) | V(old): "real-time weather and emergency alerts" [1]; flood alerts come from FWS [2] | EN/ES [1] | NF | NF | NF | NF | Free |
| Harris Co. Flood Warning System (harriscountyfws.org) | Gauge/rain by location, not per-address risk | Inundation map shows current extent only [3] | NF (gauges, not routing) | V: text/email alerts, 250+ gauges, you pick the gauge [2][3] | NF | NF | NF | NF | NF | Free |
| HCFCD MAAPnext / Flood Education tool | V(old): address floodplain lookup, flood depth grids [4][5] | NF on the MAAPnext about page (Harvey not mentioned) [4] | NF | NF | NF | NF | NF | NF | NF | Free |
| FEMA app | NF | NF | NF | V: NWS alerts for up to 5 locations [6] | EN/ES toggle [6] | NF | NF | V(old): "Recover" section, shelters [6] | NF | Free |
| FEMA Flood Map Service Center | V: enter address, get FIRM zone [7] | NF (zone only; "low risk does not rule out flooding" [7]) | NF | NF | EN | NF | NF | NF | NF | Free |
| First Street / Risk Factor | V: 1-10 score per property [8] | NF found; it is a forward model | NF | NF found | EN | NF | Partial: Realtor.com "Flood Factor", Redfin shows it [8]. Zillow pulled scores Dec 2025 [8] | NF | NF | Free basic |
| Houston TranStar | NF (roads, not addresses) | NF | Partial: ~300 sensors flag roadway flooding on its traffic map/app, no per-trip verdict [9][10] | V(old): sensor alerts on map, 3-mi radius, 90 min (2018) [11]; not per-place | NF | NF | NF | NF | NF | Free |
| AlertHouston / Houston OEM | NF | NF | NF | V: opt-in notifications [12] | Sources conflict: signup lists AR/ZH/EN/FR/ES/VI; sends EN/ES [12] | NF | NF | NF | NF | Free |
| Waze / Google Maps | NF | NF | Partly: Waze crowd reports, flood-data partnerships exist elsewhere (San Antonio) [13]; NF for Houston | Google Flood Hub urban flash-flood forecasts (2026), address-level unconfirmed [14] | Many (general) | NF | NF | NF | Maps offline areas (not verified for floods) | Free |
| Red Cross Emergency app | NF | NF | NF | V(old): flood alerts by location and hazard type [15] | EN/ES [15] | NF | NF | Shelters, recovery resources [15] | V(old): preloaded guidance offline [15] | Free |
| NWS / WEA | Polygon alerts, not address risk | NF | NF | V: Wireless Emergency Alerts, no signup (well known; no fetch) | EN; some ES | NF | NF | NF | n/a | Free |
| TX TDEM STEAR | n/a | n/a | n/a | n/a (registry that tells responders you need help) [12] | NF | NF | NF | NF | NF | Free |
| **FloodReady Houston** | Yes (FEMA zone, elevation, evac zone) | Yes (City of Houston Harvey polygons, HWMs, gauge peaks) | Yes, but only 128 known crossings | Yes (push; SMS simulated unless Twilio keys) | 5 (en/es/vi/zh/ar) UI and voice | Yes, cited, works without keys | Yes (ZIP NFIP claims, checklists) | Yes (FEMA steps, SBA, appeal) | Yes (PWA) | Free |

## 2. Our features: already solved elsewhere?

| Feature | Verdict | Who / how well |
|---|---|---|
| FEMA zone for an address | **Exists (we repeat)** | FEMA MSC [7]; we pull the same NFHL layer |
| Floodplain / depth by address | **Exists** | MAAPnext (newer, more rigorous than FEMA zone) [4][5]. We do not replace it. |
| Gauge water levels and gauge alerts | **Exists (we integrate)** | Harris FWS, USGS, NWS [2][3] |
| Weather push alerts | **Exists** | NWS/WEA, FEMA app, Red Cross, AlertHouston [6][12][15] |
| Roadway flood sensors | **Exists** | TranStar (~300 sensors) [9][10]. Real-time sensor feed is better than our static list. |
| Flood score at a home, for buyers | **Partly exists** | First Street on Realtor.com/Redfin [8]. Ours is claims-based plus Harvey, not a model score. |
| "Flooded in Harvey" next to zone for any Houston address | **Not found anywhere** (as consumer product) | Harvey data is public; a unified lookup was not found. Caveat: absence of evidence. |
| Route check against flood-prone crossings, trip verdict | **Partly exists** | Waze crowd reports; TranStar map shows hazards; no trip-level verdict for Houston found. Harris County reportedly planning a $2M driver warning system [16] (unconfirmed). Ours covers 128 crossings only. |
| Multilingual cited AI assistant (Houston) | **Not found in Houston** | No Houston/Harris chatbot found [16]. Closest: NYC FloodChat (multilingual, renters) [17]. So the idea exists elsewhere. |
| Voice in 5 languages | **Partly exists** | ReadyHarris/FEMA/Red Cross: EN/ES only [1][6][15] |
| Renter ZIP claims and buyer checklist | **Partly exists** | First Street for buyers [8]; ZIP NFIP claims view not found |
| Recovery steps (FEMA, SBA, scams, appeal) | **Partly exists** | FEMA app Recover section [6], fema.gov. We bundle by address and language. |
| Offline safety card | **Partly exists** | Red Cross offline guidance [15] |
| Storm replay with real gauge data | **Not found** | Not found as a consumer tool |
| Accountability (bond, reservoir, who is responsible) | **Not found** as a consumer product | Public docs exist; not synthesized |

## 3. Honest verdict

**Genuinely new:** the integration. One address gives FEMA zone, Harvey history, elevation, evacuation zone, nearby gauges, route check, alerts, renter/buyer data and recovery steps, in 5 languages, with a cited assistant that works without API keys. No single tool found does that. A multilingual, cited flood assistant for Houston was not found.

**Duplicate:** zone lookup, gauge data, weather alerts and sensor flooding are all official and already free. We consume them. Our alerts are not authoritative.

**Weaknesses we must own:** not an official source; route check covers 128 known crossings, not live road sensors; SMS is simulated without Twilio; MAAPnext is stronger floodplain science than FEMA zone.

### Likely judge questions
- "Doesn't ReadyHarris do this?" It is a general-prep app (EN/ES); we found no address-level risk, Harvey history or route check there.
- "Doesn't the FWS already alert people?" Yes, per gauge, and it says it is not a notification system [3]. We add place-level watch plus context.
- "Doesn't TranStar show flooded roads?" Yes, live sensors; we use them as a complement, and add a pre-trip verdict plus known-crossing history.
- "Doesn't Google/Waze route around floods?" Houston flood rerouting not found; Waze depends on crowd reports. We say check conditions, never "safe".
- "Isn't First Street the same?" It is a paid-model score for buyers (Zillow pulled it Dec 2025). We use observed Harvey data and claims, and add safety actions.
- "Is the AI reliable?" Cited, "not official guidance", 911 line, template fallback.
- "Why not just use MAAPnext?" Use it too. We link and add history, routing, language, recovery.

## 4. Positioning statement (accurate)
FloodReady Houston is not a new flood warning system. It puts what the official tools already publish (FEMA zone, Harvey flooding, gauges, evacuation zone, alerts, recovery steps) into one address-first view in five languages, with a cited assistant and a pre-trip route check on known flood-prone crossings. It is a layer on top of official sources, and it always says to call 911.

## Sources (fetched/searched 2026-10-11)
1. gov1.com ReadyHarris article: "real-time weather and emergency alerts", EN/ES (search snippet) https://www.gov1.com/emergency-management/articles/hyperlocal-emergency-apps-streamline-emergency-management-sME0vuT8JHXoUasZ/ ; https://www.readyharris.org/About (no app/language detail)
2. ReadyHarris release: FWS alerts by text/email, 250+ gauges https://www.readyharris.org/Newsroom/News-Releases/Ready-Harris-All-News-Releases/harris-county-flood-control-district-enhances-flood-warning-system-website-with-customizable-alerts
3. https://harriscountyfws.org/Help (search snippet: inundation map "not intended as a notification system"; page fetch truncated)
4. https://maapnext.harriscountytx.gov/about (fetched: depth grids; no Harvey, address search or languages stated)
5. https://communityimpact.com/lake-houston-humble-kingwood/city-county/harris-county-flood-education-tool-shows-areas-watch-storms/
6. FEMA app: https://www.nbcnews.com/news/latino/fema-launches-spanish-language-app-n183426 and fema.gov snippets (alerts for 5 locations, EN/ES)
7. https://msc.fema.gov/portal/search
8. https://www.bostonglobe.com/2025/12/01/business/zillow-climate-risk-scores ; https://bankerandtradesman.com/realtor-com-becomes-first-listings-site-to-map-flood-risk/
9. https://www.txdot.gov/about/programs/innovative-transportation/innovative-transportation-in-texas/txdots-innovation-catalog/transtar-roadway-flood-warning-system.html (fetched: "Deployed across hundreds of sensor locations")
10. https://www.memorialdistrict.org/houston-transtar-expands-local-roadway-flood-warning-system/
11. https://houston.culturemap.com/news/city-life/07-27-18-houston-flooding-app-track-real-time-transtar/ (2018)
12. https://en.wikipedia.org/wiki/AlertHouston ; https://preflight.houstontx.gov/council/committees/public-safety/20250721/oem-communications.pdf
13. https://sariverauthority.org/blog-news/expanding-our-safe-mission-with-new-waze-partnership ; https://www.phonearena.com/news/waze-to-warn-drivers-about-flooded-roads_id137665
14. https://citizen.digital/article/google-unveils-flood-hub-tool-to-predict-urban-flash-floods-n379075
15. https://apps.apple.com/US/app/id954783878 (Red Cross Emergency, EN/ES, floods) ; https://thecounty.me/?p=26687 (2014 Flood app)
16. Search results on Harris County $2M smart flood warning plan and no Houston chatbot (snippet only; unverified) , UH note on 45% non-English households https://www.uh.edu/hobby/interns/harris-fellows/harris-fellows-2023/blogs_2023/rise-of-generative-ai-provides-opportunities-for-local-government/index.php
17. https://rebuildbydesign.org/rycn-floodchat/
Hackathon check: lablab.ai "Flood Forecasting Agent" (date unclear) and NASA Space Apps 2017 WaterWaterHouston are prototypes; no Houston address+routing+multilingual-AI product found.
