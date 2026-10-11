# Verification: groups E, F, G (18 problems), Oct 11 2026

Method: read code, called the live API (:8000) and drove the UI (:5173) with Playwright at 390 px (scripts in `scratchpad/e2e/verify-EFG/`). Places: Meyerland, Addicks, Seabrook. Languages: en, es, ar (RTL). Household seeded: renter, no car, dialysis, oxygen, power device, mobility "some", 65+. 2 /ask calls, 1 /plan call. No reports or votes created. Strict rule: SOLVES only if a user at an address can complete the action in the app. None of the 18 meets that.

## Table

| ID | Verdict | Claimed (cycle 35) | One-line reason |
|---|---|---|---|
| E1 | PARTIAL | REDUCES | Household plan, go-bag, STEAR, buddy check-in work. In a warning the home screen drops "help to evacuate" and tells a no-car user to "check your route before you drive". |
| E2 | PARTIAL | REDUCES | 117-center CMS dialysis finder is real; plan says leave early. No closure or flood-exposure of the center, no storm-time trigger, note not localised. |
| E3 | PARTIAL | REDUCES | Federal relocation-rights card and letter exist. Does not solve housing; /ask on the topic omitted both the rights and the hotline. |
| E4 | INFORMS ONLY | REDUCES | Gauge peaks and ZIP claims only. No repeat-loss/mitigation, no mental-health resource anywhere. |
| E5 | INFORMS ONLY | INFORMS | IAH/HOU FAA chip on Drive only. No hospital, METRO, TMC or food bank status. |
| F1 | INFORMS ONLY | INFORMS | Sourced facts on Civic. Nothing actionable beyond "who to call". |
| F2 | PARTIAL | REDUCES | Addicks pool vs your ground works (verified). Barker has no gauge; downstream release exposure not represented. |
| F3 | NOT ADDRESSED (not app-solvable) | NONE | Only a generic Zone X risk fact. |
| F4 | INFORMS ONLY | INFORMS | 43 of 181 and the Sept 2025 restructure shown. "$864M of $2.5B" absent. Project budget/spent are null. |
| F5 | NOT ADDRESSED | INFORMS | "$165M of $834M" is not in the app, API or knowledge base. |
| F6 | NOT ADDRESSED | INFORMS | The prioritisation-score finding ($317.5M vs $187.3M) is not in the app. |
| F7 | PARTIAL | REDUCES | Named commissioner, floodplain admin and phone resolve correctly by GIS. Council member name is missing from the UI; Seabrook copy is wrong. |
| G1 | PARTIAL | REDUCES | Hotline 346-286-4020 and volunteer form on Home. Not on the Recover buyout checklist. HCFCD point layer only. |
| G2 | PARTIAL | REDUCES | Share-911-location, evac zone, SMS HELP. No "waiting for rescue" guidance; SMS distress text gets no 911 line. |
| G3 | PARTIAL | REDUCES | Mold, proof-of-loss, CO/generator card exist. Recover has no electrocution, downed-line or floodwater/infection guidance despite the claim. |
| G4 | PARTIAL | REDUCES | Declaration banner, 60-day calculator and SBA figures verified correct. The app cannot speed aid. |
| G5 | NOT ADDRESSED | REDUCES | Community hazard reports are not death/casualty data. The claim is misattributed. |
| G6 | INFORMS ONLY | REDUCES | Flood-history by address and season reminders. Nothing addresses recovering while the next storm comes. |

Counts: SOLVES 0, PARTIAL 9 (E1 E2 E3 F2 F7 G1 G2 G3 G4), INFORMS ONLY 5 (E4 E5 F1 F4 G6), NOT ADDRESSED 4 (F3 F5 F6 G5). Claimed REDUCES that fail strict reading: E4, G5, G6 (and G3 is overstated).

## Detail

### E1 Older/disabled residents. PARTIAL
- Code: `lib/summary.ts:223-236` (topActions), `pages/Prepare.tsx:234` (EvacuationHelp), `components/gobag/GoBag.tsx`, `components/buddy/BuddySection.tsx` (Watch), `backend/app/ai/plan.py:54-59`.
- Tests: Prepare/evacuate (STEAR link, 211, 311, 911, manufactured-home FEMA rule) renders in en/es/ar, RTL correct. Go-bag built from household (dialysis, oxygen, mobility, pets, no-car lines). Watch shows neighbor check-in, no errors. POST /plan (dialysis, oxygen, wheelchair, no car) returned generated_by=gemini, 8 sensible steps (STEAR, METROLift, early evacuation, 911).
- Bug (storm time): sim storm on with the household above, Home shows a Flash Flood Warning and "Do these 3 things now" = Check your route before you drive / Turn on flood alerts / Line up backup dialysis. `topActions` keeps only 3 (`summary.ts:238`), rule `['drive', level>=watch]` ignores `hasCar===false`, so "Register for help to evacuate" (`evac`) is cut. Repro: seed household hasCar=false, dialysis=true, sessionStorage floodready.demo=1 and floodready.simStorm=1, open #home.
- Gap: Gemini plan said "verify renter's insurance covers flood loss", which contradicts the app's own "renters insurance does not cover flood". Model output is not checked.

### E2 Medical dependence. PARTIAL
- Code: `components/MedicalAccess.tsx`, `services/medical.py`, `data/dialysis.json` (117 centers, CMS 23ew-n7w9), `components/prepare/PowerDependentCard.tsx`, `/empower`.
- Tests: GET /medical Meyerland returns Fmc Meyerland 1.1 mi, (832) 742-3557, 4740 W Bellfort. I confirmed this record in the live CMS API (FMC MEYERLAND, 77035, same phone). `tel:` buttons present. Power card: ZIP 77096 has 201 Medicare power-device users (emPOWER), PUC Critical Care steps, CO warning. Localised in es/ar.
- Gaps: (1) The `note` ("Distances are straight-line. Confirm hours and storm closures...") is English-only in es and ar. (2) No closure or flood-exposure data for the center itself, though `ai/live.py:350` describes get_medical as returning "flood exposure". (3) Dataset spans Harris-ish cities only (Webster to Katy). Seabrook's nearest is 5.5 mi (Clear Lake), and nothing covers Fort Bend or Galveston. (4) The "leave early" line is a static note, not tied to a warning (see E1). (5) Names are title-cased badly ("Fmc", "Usrc"). (6) /medical kind=hospital returns an empty list with "Unknown kind".

### E3 Renters displaced by buyouts. PARTIAL
- Code: `components/RentBuy.tsx:93-101` (TenantRights), `components/TenantLetter.tsx`, `data/knowledge/renters-and-buyouts.md` (49 CFR 24), `pages/Recover.tsx` list "buyout" (rec.b1-b6, KSAT 114 demolitions / 28 units).
- Tests: Meyerland renter sees "If you rent and a buyout is planned", tenant letter fills with the address (Property Code 92.0135 text). /ask "I rent and my complex is in a buyout area..." (Gemini) correctly said ask in writing about federal funds and the General Information Notice and "18 months or longer", but did not give the 346-286-4020 hotline or the URA relocation rights, and cited ProPublica for "no set timeline".
- Gap: no housing alternatives, no legal-aid contact. Rights text is conditioned on federal funds, as it should be.

### E4 Repeat flooding harm. INFORMS ONLY
- Code: `services/floodhistory.py`, `components/home/PlaceProfile.tsx`; Recover b3.
- Test: Meyerland history lists Tax Day 41.98 ft minor, Harvey 45.66 ft major, Imelda 39.18 ft action, June 2026 28.87 ft normal, and ZIP peak 2017 with 2,550 claims. All are gauge peaks 2.9 mi away, not "this home flooded". grep for 988 / mental / PTSD / distress in frontend, knowledge and API finds nothing.
- Gaps: no Severe Repetitive Loss lookup (county-wide count only, in a Recover list item), no ICC/elevation/mitigation pointer, no mental-health or Disaster Distress Helpline. The coverage doc marks this REDUCES; it is not.

### E5 Critical services shut down. INFORMS ONLY
- Code: `components/p35/P35.tsx:AirportChip`, `pages/Drive.tsx:160`, `routers/airports.py`.
- Test: Drive shows "IAH: open | HOU: open" with FAA source and "closures only, not weather". Note the chip is wired only on Drive (cycle-35 doc said no UI, now there is one). API /airports/status live.
- Gaps: hospitals, TMC, METRO/rail, food banks, dialysis closures: nothing.

### F1 Aging reservoirs. INFORMS ONLY
- Civic Addicks: Texas Tribune "high risk of failure... $100M" fact with source. No dam status or Corps data. Not app-solvable.

### F2 Reservoir releases. PARTIAL
- Code: `routers/reservoir.py` GET /reservoir/pool?lat&lon (lat/lon required), Civic card.
- Tests: Addicks area: pool 83.74 ft (action 93, minor 96, Harvey crest 109.1), ground 92.1 ft, "about 8.4 ft below ground; in Harvey ~17.0 ft above". Datum caveat shown. Meyerland: in_area false, card hidden, as expected. Buffalo Bayou downstream (29.7615,-95.5101): reservoir_area false, no release-risk message, `barker:null`.
- Gaps: no Barker pool; downstream-release exposure (the actual problem) is not modelled; Addicks "area" is approximate.

### F3 Development paving. NOT ADDRESSED
- Only the generic "Flat clay terrain..." fact in /risk. Nothing on development. Not app-solvable.

### F4 Bond behind schedule. INFORMS ONLY
- Civic/API: "43 of 181 complete (auditor memo via Fox 26)" and the Sept 2025 restructure (75/26/15/54). Missing: "$864M of $2.5B spent". Projects near the point have `budgeted:null, spent:null`. The copyable message names a project (Meyerland: a federal Corps Brays project; Seabrook: trailing space in "A104-00-00 ").

### F5 Partner funding. NOT ADDRESSED
- grep for 834/165 across frontend, backend, knowledge: no hits.

### F6 Spending vs priority. NOT ADDRESSED
- grep for 317.5/prioritiz: no hits.

### F7 Fragmented governance. PARTIAL
- Code: `services/officials.py` (GIS point lookups), `components/WhoToContact.tsx`, `pages/Civic.tsx`.
- Tests: Meyerland: Rodney Ellis Pct 1, Council District C (832-393-3004), floodplain admin Choyce Morrow. Addicks: Briones Pct 4, District A. Seabrook: Garcia Pct 2, admin Nick Kondejewski (City of Seabrook), no council (correct). The ProPublica "Nobody's in charge" quote is shown with source.
- Bugs: API returns the council member (Abbie Kamin, Amy Peck) but the UI shows only "Council District C"/"A". Seabrook (own city and admin) shows "Unincorporated Harris County... Outside city limits" and "The Houston 311 portal..." copy.

### G1 Buyouts slow/unknown. PARTIAL
- Code: `components/p35/P35.tsx:BuyoutContact` (in RentBuy), `services/buyouts.py` (HCFCD point layer, 0.5 mi).
- Tests: Home > Renting or buying: hotline `tel:+13462864020`, general 346-286-4000, survey form, "The HCFCD page gives no timeline". Recover buyout checklist (expanded): no hotline (`'4020' in text` false). Buyout area false for Meyerland and Buffalo Bayou test point.
- Gaps: layer is HCFCD "areas" only; City of Houston and other programs, and application status, are not covered. The 18-month figure appears only as a KSAT quote.

### G2 Rescue overload. PARTIAL
- Code: `RecoverExtras.tsx:Share911`, `services/sms.py`, `/evac`.
- Tests: SMS simulate "HELP" gives help text with 911; "77096" gives risk plus 911. "I am stuck in my attic and water is rising" returned "could not find that place..." with no 911 line (`sms.py` not-found template lacks `c911`). A phone that once sent "AYUDA" gets Spanish for later English "HELP" (sticky language; design choice, but unexpected).
- Gaps: no guidance for waiting on rescue (go up, signal, do not enter attic without exit); coordinates sharing is browser geolocation only.

### G3 Post-flood hazards. PARTIAL
- Code: Recover (`RecoverExtras.tsx` mold card, `PowerDependentCard` CO), knowledge `post-flood-safety.md`.
- Test: grep of frontend for electric/downed/floodwater/contaminat finds only storm-time strings (p37). Recover dump (en, es, ar) has no electrocution or contaminated-water section; mold has 4 bullets (EPA). /ask on post-flood hazards (Gemini unavailable, template) returned one bullet: stay out of floodwater, away from downed lines; infection was not mentioned.
- Cycle-24 claim "Post-flood hazard guidance in Recover" is false in the current UI. The 4 Harvey electrocutions and Imelda death are only in the Ask knowledge base.

### G4 Aid slow. PARTIAL
- Code: `services/declarations.py`, `DeclarationBanner` in Recover, `RecoverExtras.tsx:ProofOfLoss`, `SbaAndDebris`.
- Tests: FEMA OpenFEMA check: Harris DR-4798 Beryl has ihProgramDeclared=true, iaProgramDeclared=false; no later Harris declaration (including after the June 2026 flood). Banner: "No active federal individual-assistance declaration... (latest: DR-4798 Hurricane Beryl, Jul 9, 2024)" is correct and localised. Proof-of-loss date math checked: 2026-10-01 -> 11/30/2026 (50 days left), 2026-01-01 -> 3/2/2026 "passed", 2026-02-28 -> 4/29/2026. SBA text ($500,000 home repair, $100,000 personal property, insurance may be deducted) matches SBA physical-damage loan limits. Photo helper and recovery tracker are local only.
- Gap: the tracker/aid steps tell users to expect delays; the app cannot speed FEMA. The "aid" checklist step 3 admits "We do not have verified grant amounts, deadlines".

### G5 Flood-death data fragmented. NOT ADDRESSED
- `/reports` is empty (GET); reports are hazard reports (6 h window in API, 24 h in Recover UI). No casualty data. HWM and Harvey extent are consistent datasets but not deaths.

### G6 Back-to-back storms. INFORMS ONLY
- Flood history events, storm-season .ics (Nov 1 monthly, STEAR Apr/May, go-bag May 18, season Jun 1), mention in knowledge. No feature handles "recovering while the next warning hits".

## Ranked bug list
1. (E1/E2) Warning-time top actions: no-car/medical household gets "Check your route before you drive" and loses "Register for help to evacuate"; no personalised "leave now" message. `lib/summary.ts:228-238`.
2. (G3) Recover has no post-flood electrical/floodwater/infection guidance; docs claim it does. Content exists only in `data/knowledge/post-flood-safety.md`.
3. (G2) SMS distress text ("stuck in attic, water rising") returns "could not find that place" without a Call 911 line. `services/sms.py` not-found template.
4. (F5/F6/F4) Audit numbers missing: $165M of $834M, $317.5M vs $187.3M, $864M of $2.5B. Add sourced facts to `services/civic.py` and the knowledge card.
5. (E2) Medical note English-only in es/ar; no facility closure or flood-exposure; coverage limited to ~Harris cities; live.py describes flood exposure that the API does not return.
6. (F7) Council member name not rendered; Seabrook gets "Unincorporated Harris County / Houston 311" copy.
7. (G1) Hotline missing from Recover buyout checklist; HCFCD-only layer.
8. (E3) /ask for renter buyout misses the hotline and URA rights card; weak citation.
9. (E4) No mental-health/Disaster Distress resource, no SRL or mitigation (ICC/elevation) pointer.
10. (E1) Gemini plan can contradict app copy on renters flood coverage.
11. Coverage doc overstates: E4, G5, G6 are not REDUCES; G3 overstated. Honest recount for E/F/G: 0 solved, 9 partial.
