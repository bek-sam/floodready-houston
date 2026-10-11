# Cycle 38 research: unmet needs, each buildable in 1 h or less (no code edited)

Checked 2026-10-11 (~8 AM). Already in the app, so not repeated: STEAR / 2-1-1 / 311 (`EvacuationHelp.tsx`, `special-needs-and-no-car.md`), power-dependent medical devices (cycle 27), tenant flood-disclosure and relocation rights (cycles 27-28), FAA airport chip (cycle 35). A grep of `frontend/src`, `data/knowledge` and `backend/app` found **no** mention of AlertHouston, KTRH, KUHF, ridemetro, MetroLift, or boil water. CenterPoint appears only as a name inside one knowledge card.

Recount note: none of these moves a problem from INFORMS to REDUCES on its own, because each is a link-out card. Honest tags are given per item. Pitch no change to 37/52.

## 1. Power outage: CenterPoint tracker, report line, Power Alert Service
- **Who:** every resident; most of all medical-device households, because the existing card says "register" but never says how to see whether your block is out.
- **Source:** https://www.centerpointenergy.com/en-us/residential/services/electric-utility/outage-center (HTTP 200, fetched with curl). Page text: "Outage Tracker: View real-time updates on electric outages and estimated restoration times"; "Report an outage: Start an online report or call 713-207-2222"; "Sign up for Power Alert Service: Receive free alerts from CenterPoint Energy on outages and power restoration in your area." The tracker link on that page is https://tracker.centerpointenergy.com/map/texas. It loads a DataCapable map app. It has no documented API.
- **Data:** none free or keyed that I could find. Link out only. Do not scrape it.
- **App today:** `power-dependent-medical.md` mentions CenterPoint only in passing. There is no tracker link and no phone number.
- **Smallest addition:** three buttons in `PowerDependentCard.tsx` and on the Alerts page: Outage Tracker, `tel:713-207-2222` (labelled "report a non-emergency outage"; downed lines are "Call 911"), and Power Alert sign-up. Add a line to the knowledge card with the same sources.
- **Effort:** 20 min, plus strings in 5 languages.
- **Converts:** E5 stays INFORMS (it is a utility, not a hospital or transit shutdown). It deepens E2 and G3, which are already REDUCES.

## 2. People without a car: METRO alerts, MetroLift, text alerts
- **Who:** carless households and paratransit riders. E5 cites bus and rail shutdowns in Allison and Imelda. The app has no METRO information.
- **Source:**
  - https://www.ridemetro.org/alerts/service-alerts-and-detours (200). Page text: "Save time and avoid delays by receiving alerts directly to your email or phone." It points to the RideMETRO app and METRO's Facebook and X accounts.
  - https://www.ridemetro.org/alerts/text-and-email-alerts-newsletters (200).
  - https://www.ridemetro.org/riding-metro/transit-services/metrolift-paratransit (listed on the homepage).
  - METRO customer service: 713-635-4000, call or text; TTY 713-635-6993 (homepage).
- **Data:** METRO's official alerts feed is https://api.ridemetro.org/v2alertspb/alerts.pb. I tested it with no key and got HTTP 401 "Access denied due to missing subscription key". The developer portal (https://api-portal.ridemetro.org/) says "You will need to subscribe to the APIs" using a Microsoft or Google account, and does not state whether a key is free. **Do not build a live feed today.** The portal also offers JSON `v2alerts/alerts`. Park it for after the hackathon.
- **App today:** nothing.
- **Smallest addition:** a "No car? Check transit before you go" card on Drive and Prepare with 3 links, the 713-635-4000 number, and one honest line: "Transit can stop during floods; this app does not show live METRO status." Do not state any suspension policy. I found only news reports from Harvey and 2019 (https://masstransitmag.com/safety-security/press-release/12363700/...), not a METRO policy page.
- **Effort:** 20 min.
- **Converts:** E5 partial. It stays INFORMS, like the airport chip.
- **Gap, stated honestly:** I found no verified current City of Houston or Harris County program that picks up carless residents for hurricane evacuation. The search returned only 2005 and 2017 stories. The app should keep sending people to 2-1-1 / STEAR and must not invent a pickup service.

## 3. Alert sign-up and local-language broadcast sources (Spanish and Vietnamese)
- **Who:** non-English speakers and anyone whose phone or power is down (battery radio).
- **Source, verified:**
  - AlertHouston, https://houstonoem.org/ (200). Page text: "Register for alerts through email, text message or voice call." The app does not link it. Wikipedia says OEM sends in English and Spanish, but I could not confirm that on the city page. Do not state it.
  - Ready Houston "Media and Weather", https://www.readyhoustontx.gov/?p=600. Page text: "KTRH AM 740 is Houston's Emergency Alert System station." "KUHF FM 88.7 is Houston's Public Radio station." Univision, Telemundo and Multimedios affiliates "provide local news, weather, and traffic in Spanish." The page gives no call signs or frequencies for the TV stations. It lists **no** Vietnamese media.
  - NWS Houston/Galveston Spanish hurricane guide, https://www.weather.gov/hgx/hurricaneguide2026_spanish (200). PDF: https://www.weather.gov/media/hgx/hurricanes/2026HurricaneGuide/HurricaneGuide2026_Spanish.pdf (200, application/pdf).
  - Vietnamese radio: KREH "Radio Saigon Houston", 900 AM, "operates from sunrise to sunset", relayed on 99.7 FM by K259DC (https://en.wikipedia.org/wiki/KREH). **Wikipedia only.** The station's own site, radiosaigonhouston.com, did not respond, so the frequency is unverified from an official page. A daytime-only AM station is not an overnight flood-alert source. Say so, or leave it out. PRI documents that it struggled to stay on air during power outages in Hurricane Ike (https://www.pri.org/stories/2008-09-30/radio-saigon-houston-keeps-vietnamese-community-informed-during-hurricane-ike).
- **Data:** none needed.
- **App today:** language support is in the UI (5 languages), but there is no "where to hear alerts in your language" list.
- **Smallest addition:** a "Hear alerts without internet" card on Alerts and the go-bag checklist (a battery radio item already exists? check `gobag/items.ts`). Items: AlertHouston link, KTRH 740 (EAS), KUHF 88.7, Spanish-language TV by affiliate name only, NWS Spanish hurricane guide. Show KREH only as "Vietnamese radio: confirm hours and frequency at the station" until an official source is checked.
- **Effort:** 30 min.
- **Converts:** D5 (language gaps) and D2/D3 depth. These problems are probably REDUCES already, so no new credit, but this closes the Vietnamese-speaker and power-out gap.

## 4. Boil-water and drinking-water safety after a flood
- **Who:** flooded households, and Houston residents at large when water pressure fails (Nov 2022 citywide notice).
- **Source:**
  - TCEQ, https://www.tceq.texas.gov/drinkingwater/notices/bwn/understanding-bwns (fetched). A notice means water "may be unsafe for consumption or may pose an acute health risk." Boil at a "vigorous rolling boil" for two minutes. Use boiled water for teeth, ice and baby formula. Boil even with a home filter. Natural disasters are listed as a cause of notices. For questions, PWSNotice@tceq.texas.gov, or call your water system.
  - Houston Public Works, https://www.houstonpublicworks.org/boil-water (200). It is a **lifted 2022 press release** ("City of Houston Lifts Boil Water Notice", Nov 29, 2022), so it is not a live notice page.
- **Data:** no current statewide active-notice list exists. TCEQ's only list I found is the 2021 winter-storm snapshot. A live feed is **not available**.
- **App today:** nothing.
- **Smallest addition:** a card on the After-a-flood page (`Recover.tsx`): "If you get a boil-water notice (or your water looks cloudy or the pressure drops)", with the TCEQ boil steps and "ask your water supplier; Houston 311". Source the steps to TCEQ. Do not claim Houston will push a notice to the app.
- **Effort:** 20 min.
- **Converts:** nothing (G3 is already REDUCES). It is a real safety gap, though.

## 5. School and childcare closures (low confidence, optional)
- **Who:** parents deciding on a school run during a flash flood (D4 gives little warning).
- **Source:** the Houston ISD site (200) and the Back to School guide, https://www.houstonisd.org/backtoschool, which says to text YES to 68453 for weather alerts. The inclement-weather hotline differs between HISD pages (713-556-9595 vs 713-267-1704). I could not confirm the 2026 status of either number.
- **Smallest addition:** one line, "Check your own school district's site or text alerts; closures are decided district by district." Link to houstonisd.org only. **Do not print the 68453 code or a hotline number** until someone checks the current HISD page. Many Harris County children are in other districts.
- **Effort:** 10 min. **Converts:** nothing.

## Checked and not recommended
- **Apartment ground-floor and garage flooding.** I found no authoritative source on garage or ground-floor duties. The statute (Tex. Prop. Code 92.0135, https://texas.public.law/statutes/tex._prop._code_section_92.0135) is already used in the app. A secondary landlord guide claims SB 2349 changed the notice rules, which I could not verify, so do not add anything.
- **METRO live feed.** It needs a subscription key (401 verified above).
- **CenterPoint live data and a third-party outage map.** There is no documented API, and poweroutage.us returned 403. Link out only.
- **houstonemergency.org.** It returned HTTP 500 today, and the search pointed to it for boil-water updates. The OEM site is now https://houstonoem.org/. Do not cite the old domain.

## Suggested order, 1 h total
1. AlertHouston plus broadcast card (item 3, 30 min).
2. CenterPoint buttons (item 1, 20 min).
3. METRO links (item 2, 20 min).
4. Boil-water card (item 4) only if there is time.
All of these need `tel:` or link-out only, no keys, and the "Call 911" and "not official guidance" wording. Add i18n strings in en, es, vi, zh and ar.
