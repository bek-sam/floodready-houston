# Data sources (verified 2026-10-10 from this machine unless marked "untested")
Legend: ✓ = live call returned valid data; ✗ = failed/blocked; ? = not tested (from docs/search only).

## Core hydrology / weather
| Source | URL | Auth / limits | Format | Status | Used by |
|---|---|---|---|---|---|
| USGS OGC API (current) | `https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-continuous/items?monitoring_location_id=USGS-08074500&f=json` | No key works; api.data.gov key optional for higher limits (via `X-Api-Key`/`api_key`). Responses pass through api-umbrella (rate-limited per IP; not published in headers). | GeoJSON; `properties.time,value,parameter_code` (00060 discharge cfs, 00065 stage ft) | ✓ | gauges on risk card, route-check |
| USGS OGC API (historical IV) | `.../collections/continuous/items?monitoring_location_id=USGS-08074500&parameter_code=00065&time=2017-08-27T00:00:00Z/2017-08-27T03:00:00Z&limit=3&f=json` | same | GeoJSON, 15-min values; Harvey 2017 stage returned (13.46 ft at 2017-08-27 00:00Z at Buffalo Bayou, 08074500). Use `limit` + `time=a/b` interval. | ✓ | Storm Replay |
| USGS OGC daily | `.../collections/daily/items?monitoring_location_id=USGS-08074500&time=2017-08-26/2017-08-28` | same | GeoJSON (Harvey daily mean 30200 cfs) | ✓ | replay fallback |
| USGS legacy `waterservices` IV | `https://waterservices.usgs.gov/nwis/iv/?format=json&sites=08074500&period=PT2H` | none | WaterML-JSON | ✓ (works now) | fallback only. **Decommission: Feb 22 2027 (USGS blog https://waterdata.usgs.gov/blog/api-waterservices-decom/); intentional degradation possible from Aug 2026.** Don't build on it. |
| NOAA NWPS | `https://api.water.noaa.gov/nwps/v1/gauges/{LID}` ; list by bbox `.../gauges?bbox.xmin=-95.8&bbox.ymin=29.4&bbox.xmax=-95.0&bbox.ymax=30.1&srid=EPSG_4326` ; observed/forecast `.../gauges/{LID}/stageflow` | none | JSON (lid, usgsId, flood stages, lat/lon) | ✓ (bbox list + gauge detail; ADDT2 = Langham Creek at Addicks Reservoir is in the list). Note `BYST2` does not exist - get real LIDs from the bbox list. | flood stages, forecasts |
| NWS alerts | `https://api.weather.gov/alerts/active?point=29.76,-95.37` | **User-Agent header required** (`FloodReadyHouston/0.1 (email)`); no key; be polite (~<1 req/s) | GeoJSON; `properties.event, severity, headline, description, expires` | ✓ | alerts, voice alerts |
| NWS event names | `https://api.weather.gov/alerts/types` (list of 100+ names) | same | JSON | ✓ | filter to: `Flash Flood Warning`, `Flash Flood Watch`, `Flood Warning`, `Flood Watch`, `Flood Advisory`, `Flash Flood Statement`, `Flood Statement`, `Coastal Flood Warning/Watch/Advisory`, `Tornado Warning`, `Hurricane/Tropical Storm Warning/Watch`, `Storm Surge Warning/Watch`. Alerts have `severity` (Extreme/Severe/...) and `urgency`. |
| Open-Meteo | `https://api.open-meteo.com/v1/forecast?latitude=29.76&longitude=-95.37&hourly=precipitation&forecast_days=1` ; archive: `https://archive-api.open-meteo.com/v1/archive` (?) | No key, free for non-commercial; ~10k calls/day | JSON | ✓ forecast; archive ? | rainfall next 24h on risk card |

## Risk / geo
| Source | URL | Auth / limits | Status | Used by |
|---|---|---|---|---|
| FEMA NFHL layer 28 (S_FLD_HAZ_AR) | `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?geometry=-95.37,29.76&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF&returnGeometry=false&f=json` | none; occasionally slow/timeouts - set 15s timeout, cache by rounded lat/lon | ✓ (downtown returned `X / AREA OF MINIMAL FLOOD HAZARD / F`) | FEMA zone |
| USGS EPQS | `https://epqs.nationalmap.gov/v1/json?x=-95.37&y=29.76&units=Feet&wkid=4326` | none | ✓ (`value`: 47.19 ft; note: far from Open-Meteo's 20 m grid elevation - EPQS is the better source) | elevation / low-ground |
| US Census geocoder | `https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=...&benchmark=Public_AR_Current&format=json` | none | ✓ (US street addresses only; fails on landmarks/partials) | /geocode primary |
| Nominatim | `https://nominatim.openstreetmap.org/search?q=...&format=json&limit=1` | **Policy: max 1 req/s, valid identifying User-Agent, no autocomplete/bulk, cache results** (https://operations.osmfoundation.org/policies/nominatim/) | ✓ | geocode fallback (landmarks) |
| OSRM demo | `https://router.project-osrm.org/route/v1/driving/{lon,lat};{lon,lat}?overview=full&geometries=geojson&alternatives=true` | Demo server (FOSSGIS): fair use, ~1 req/s, no heavy/bulk use, no SLA. OK for a hackathon demo with caching; don't loop it. | ✓ | route-check. Keep a straight-line fallback + pre-cached demo routes. |
| OSM tiles | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | tile usage policy: attribution, no bulk; fine for demo | ? | map |

## Houston-area flood data
| Source | URL | Auth | Status | Notes / feature |
|---|---|---|---|---|
| TranStar flood sensors (sample) | `https://traffic.houstontranstar.org/api/roadwayfloodwarning_sample.json` | none | ✓ | static sample from 2024-02-13; fields: SensorId, SensorName, Latitude, Longitude, TopOfBank, Precipitation*, StreamElevation*, alert flags -> crossings seed |
| TranStar flood sensors (live) | `https://traffic.houstontranstar.org/api/roadwayfloodwarning.json` | access by request | ✗ 403 | cannot use; use sample + own crossings |
| Harris County FWS | https://www.harriscountyfws.org/ | none | ✓ site loads, **no API** (350+ gauges; data delayed ~5 min). Unofficial scraper: https://github.com/dcbark01/HouFloodScraper | link-out only; use USGS/NWPS for equivalent gauges |
| HCFCD ArcGIS org (public, no auth) | org id `nLl0k0Mja5hnSeSl`, base `https://services2.arcgis.com/nLl0k0Mja5hnSeSl/arcgis/rest/services/` | none, standard ArcGIS REST `query?where=1=1&outFields=*&f=geojson&outSR=4326` | ✓ | see next table |
| Rice TaxDay dashboard / MAAPnext | MAAPnext: https://maapnext.harriscountytx.gov/Understand-Your-Risk , https://www.hcfcd.org/MAAPnext ; Rice: https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk | - | ? (no API/download found) | cite facts only; link-out |
| City of Houston Harvey Inundation | `https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4` (polygon, 350k features, estimate to 8/31/2017, riverine only; modified behind Addicks/Barker using 109 ft / 102 ft elevation cutoffs) | none | ✓ layer metadata + count; slow (>25 s for point query) | "was my address inundated in Harvey" point-in-polygon; **pre-extract/simplify offline, do not query live** |
| Harris County Harvey Peak Inundation | https://services.arcgis.com/mB8BV33S4QhyHRrC/arcgis/rest/services/Harvey_Peak_Inundation/FeatureServer (layer id not 0 - list layers) | none | ? service listed in ArcGIS search | alt Harvey extent |
| Fort Bend Barker Reservoir Inundation | `https://gisportal.fortbendcountytx.gov/arcgis/rest/services/Hosted/Barker_Reservoir_Inundation_Map/FeatureServer` (12+ polygon layers, one per pool elevation e.g. ..._96 to _107; layer 0 has 40 polygons) | none | ✓ | **Barker reservoir pool polygons by elevation** -> `reservoir_area`. Only Fort Bend side; Harris side not found. |
| USACE Addicks/Barker (BBTRS) | ArcGIS Online owner `usace_kds` (e.g. https://services5.arcgis.com/1Q69X8bhNiDzwAVJ/arcgis/rest/services/BBTRS_Study_Area_Map/FeatureServer); also `HCFCD Addicks Reservoir Maximum Inundation Spillway Potential` web map (owner Matthew.Barr) | none | ? listed, not queried | candidate Addicks/Barker boundary; verify layer before use. Fallback: hand-drawn polygon in data/ from USACE 100-ft pool contour |
| HCFCD 2018 Bond (project points) | `.../HCFCD_Bond_Points/FeatureServer/0` (180 pts; fields Type, BondID, Match, Status) | none | ✓ | **bond projects near you** (/civic) |
| HCFCD Bond CIP structural | `.../Bond_CIP_Structural_CJO/FeatureServer/0` (87 pts: Project_Title, Watershed, Precinct, Benefits, Funded, Budgeted, Spent, Status, Total_Bond_Allocation, Hyperlink) | none | ✓ | **best bond layer**: budget vs spent per project |
| HCFCD bond detention basins | `.../HCFCD_Bond_Detention_Basins_Bond/FeatureServer/0` (69 polygons) | none | ✓ | basin overlay |
| HCFCD Flood Reference Marks | `.../HCFCD_Flood_Reference_Marks/FeatureServer/0` (1,423 benchmark points; surveyed elevation marks, NOT Harvey high-water marks) | none | ✓ | do not label as HWM |
| Other HCFCD layers (listed in ArcGIS search, unqueried) | `HCFCD_LOMR_Updated_Floodplains_FL_20170103`, `HCFCD_FWS_Boundary`, `M3_HCFCD_Drainage_Network`, `HCFCD_All_ROW`, `City_Limit_Boundaries_FL` | none | ? | jurisdiction (B11) via `City_Limit_Boundaries_FL`; drainage network for B8 |
| HCFCD bond project list/dashboard (web) | https://www.hcfcd.org/2018-bond-program/bond-program-project-list ; https://hcfcd.org/bond-program | - | ✓ pages exist, no download found | link-out |
| Harvey high-water marks (USGS STN) | `https://stn.wim.usgs.gov/STNServices/HWMs/FilteredHWMs.json?Event=135&States=TX` (event id from memory, **untested**; verify at https://stn.wim.usgs.gov/STNDataPortal) | none | ? | possible "Harvey water reached X ft here" fact |
| City of Houston open data | https://data.houstontx.gov and ArcGIS `https://geogimsms.houstontx.gov/arcgis/rest/services` | none | ✓ ArcGIS server up; open-data portal not tested | flood items found: Harvey inundation (above) |
| Search ArcGIS Online | `https://www.arcgis.com/sharing/rest/search?q=<terms>&f=json&num=20` | none | ✓ | use to discover more layers |

## Risk notes
- **Rate-limit risks**: Nominatim 1/s, OSRM demo ~1/s, NWS polite, FEMA/Houston ArcGIS slow -> cache every call (key = lat/lon rounded to 3 dp) and pre-seed demo addresses (downtown, Meyerland, Kingwood, Addicks area).
- Gemini quota is per project and not published as a fixed table (see stack.md) -> cache answers, template fallbacks.
- Bond audit stats (43 of 181 done, $165M of $834M) come from research-brief.md; the live layers give per-project spend to cross-check.
