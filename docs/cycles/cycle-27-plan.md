# Cycle 27 plan (freeze 11 AM; each item <= 1.5 h)

Source research: docs/cycles/cycle-27-research.md. Rule: a fact we cannot verify is REMOVED, not reworded.

## Builder assignments (one per folder)
- **DATA** (data/, scripts/, docs/): P1-A, P1-B, P1-C, P1-D data side, P2 knowledge cards, re-record snapshots.
- **BACKEND** (backend/ excl. app/ai): P1-E (one-line risk.py fix), P1-D code-by-fact change, P2 `/empower`.
- **AI** (backend/app/ai): P2 only: optional `get_power_help` tool; confirm RAG picks up new cards. Nothing else.
- **FRONTEND** (frontend/src): P1 i18n edits (5 langs), P2 card in Prepare.

## PRIORITY 1: wrong or stale facts

### Gotcha: civic i18n is index-keyed
`backend/app/services/civic.py` builds codes `civic.bond.{i}` / `civic.res.{i}` from list position, and `frontend/src/i18n/p12.ts` translates by code. Deleting a fact from `data/civic.json` shifts every later index and mis-translates. Fix (BACKEND, 5 lines): use `f.get("code")` and fall back to the index. DATA then adds explicit `"code"` to every remaining fact (keep today's codes: remaining bond facts keep `civic.bond.0`, `.4`, `.5`; reservoir facts keep `civic.res.0..3` slot numbers). FRONTEND deletes the dead keys.

### P1-A. "extremely high risk" (NOT in the cited Texas Tribune article)
Source for replacement: https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/ (Corps: "a high risk of failure due to seepage and piping"; repairs "more than $100 million").
Places (replace in all):
- data/civic.json reservoir.facts[0]
- data/knowledge/reservoirs-and-dams.md line 6
- backend/app/services/risk.py line 70 (fact.dams text)
- frontend/src/i18n/p12.ts: `fact.dams` lines 21, 133, 245, 357, 469 (en/es/vi/zh/ar) and `civic.res.0` lines 87, 199, 311, 423, 535
- research-brief.md line 47 (lead-owned; lead must edit; the Tribune link does not support the phrase)
- data/demo_snapshot/GET__api_civic-*.json (4 files; regenerate, do not hand-edit)
Corrected text:
- civic.res.0: "Addicks and Barker reservoirs date from the 1940s. Since 2004 the Army Corps of Engineers has found a high risk of failure due to seepage and piping; more than $100M in repairs were needed, and not all are complete."
- fact.dams: "You are near the Addicks/Barker reservoirs (1940s dams that the Corps has found at high risk of failure from seepage and piping); Harvey releases flooded homes downstream."
- md line 6: drop `rated "extremely high risk."`; keep the Corps quote. The clause "the 2010 risk document was never made public" is not verified in research: DATA must confirm it in the Tribune page within 5 min or delete it.

### P1-B. "167,000 acres developed in the decade after Allison"
Only in data/knowledge/reservoirs-and-dams.md line 8. Not on the cited ProPublica page. DELETE the line. Do not replace with another number. (Optional verified substitute from the research: ProPublica reports the Corps bought ~24,500 acres and ~8,000 more could flood: https://projects.propublica.org/graphics/harvey-reservoirs . Use only if DATA re-reads the page first.)

### P1-C. "Neither the city nor the county requires flood disclosure"
Misleading today (Texas Prop. Code 92.0135 landlord flood notice since 1 Jan 2022; seller disclosure of floodplain/reservoir status since SB 339, 2019: https://capitol.texas.gov/tlodocs/86R/analysis/pdf/SB00339S.pdf). Contradicts data/knowledge/tenant-flood-disclosure.md. Places:
- data/civic.json reservoir.facts[3]; data/knowledge/reservoirs-and-dams.md line 9; data/knowledge/renters-and-buyouts.md line 8
- frontend/src/i18n/p12.ts `civic.res.3` lines 90, 202, 314, 426, 538
- frontend/src/i18n-extra.ts `rec.b1` lines 41, 87, 155, 223, 291 and frontend/src/i18n-fill.ts `rec.b1` lines 831, 1616 (FRONTEND: `grep -rn "rec.b1\|rec.b'" frontend/src` for any other copy; the zh/ar copies exist twice)
- demo_snapshot civic files (regenerate)
Corrected text:
- civic.res.3: "As of 2017 ProPublica reporting, Harris County and Houston did not require flood-risk disclosure to buyers beyond a plat note near the reservoirs. Texas law has since added a landlord flood notice (Property Code 92.0135, since 2022) and a seller's disclosure of floodplain and reservoir status (SB 339, 2019)." Sources: ProPublica URL above + SB 339 URL. (The "plat note" applies to Barker only per the source; keep it out of the sentence if unsure.)
- renters md line 8: "ProPublica reported in 2017 that neither the city nor the county required flood-risk disclosure; a renter said: 'When I started to rent this house, nobody told me.' Texas now requires landlords to give written flood notice (Property Code 92.0135, see tenant-flood-disclosure.md)." Keep the quote.
- rec.b1: "Renters: Texas landlords must give you a written flood notice (Property Code 92.0135). Ask in writing about past flooding too." Translate to es/vi/zh/ar.
- reservoirs md line 9: replace with the civic.res.3 text.

### P1-D. Bond figures
Verified by Fox 26 only: 43 of 181 and the ~$1.3B shortfall. Fix wording and remove unverified numbers.
- bond.0 (civic.json, flood-bond md line 8, p12.ts `civic.bond.0` lines 80, 192, 304, 416, 528): "Harris County auditor memo, June 2025: by March 2025, 43 of 181 bond project groups in the 2018 flood bond program were complete." (source: Fox 26 https://www.fox26houston.com/news/harris-county-flooding-projects-budget-shortfall plus the memo). In md line 8 delete "and $864M of $2.5B had been spent".
- DELETE (unverified; memo PDF not readable): `$864M spent` (civic bond.1; p12.ts 81,193,305,417,529), `$834M/$165M FRT` (bond.2; md line 10; p12.ts 82,194,306,418,530; docs/sources.md line 51), `$317.5M vs $187.3M` (bond.3; md line 11; p12.ts 83,195,307,419,531). Exception: if DATA opens the PDF in a browser in 10 min and reads the numbers, keep them and say so in the commit note.
- bond.5 (restructure; civic.json, flood-bond md line 9, p12.ts 85,197,309,421,533): "In September 2025 the county restructured the 2018 bond program: of 116 remaining project packages, 75 are moving forward, 26 are paused and 15 were closed as not feasible; 54 packages were already complete. Check the HCFCD dashboard for current status." Source: https://cp4.harriscountytx.gov/Connect/Newsroom/flood-bond (replace the Cypress article, which lists only 4 active/5 paused). Add "A later $400M shortfall (down from ~$1.3B)" only with the Fox 26 source and only if DATA confirms the wording; otherwise omit.
- Replace the dropped facts in docs/sources.md line 51.
- devpost.md, judge-qa.md, README: grep found none of these figures; no change needed. DATA re-run `grep -rniE "864|165 million|317|extremely high|167,000|requires.*disclos" docs README.md data frontend/src backend/app` as the final check.

### P1-E. Unchanged but double-check
"Neither ... 4,000 built after Allison" -> change "about 4,000" to "at least 4,000" (source wording) in civic.json, md line 7, p12.ts `civic.res.1`. "more than 300,000 vehicles" should read "a little more than 300,000" only if it appears as exact; low priority.

## PRIORITY 2: power-dependent medical devices (all folders)

### Backend: `GET /api/empower?zip=77096`
New `backend/app/services/empower.py` + `routers/empower.py` (register in main.py). Call
`https://services2.arcgis.com/ZQ4jTQn6k7VPXEwO/arcgis/rest/services/HHS_emPOWER_REST_Service_Public/FeatureServer/1/query?where=Zip_Code%3D'{zip}'&outFields=Zip_Code,Medicare_Benes,Power_Dependent_Devices_DME,O2_Services_Any_DME,Facility_ESRD_Dialysis_Any_DME&returnGeometry=false&f=json` via the shared http cache (ttl 7 days; validate zip with `^\d{5}$`). Response:
```
{zip, medicare_benes:int|null, power_dependent_devices:int|null, oxygen:int|null, dialysis:int|null,
 available:bool, source:"https://catalog.data.gov/dataset/hhs_empower_rest_service_public",
 map:"https://empowerprogram.hhs.gov/empowermap",
 note:"Medicare beneficiaries only. Counts for the ZIP, not individuals' locations.",
 puc:{url:"https://www.ercot.com/files/docs/2024/01/17/PUC-Critical-Care-Form.pdf", note:"Critical care designation does not guarantee uninterrupted power or faster restoration."},
 co:{url:"https://www.cdc.gov/carbon-monoxide/about/index.html"}, meta, warnings?}
```
Failure or empty feature: `available:false`, counts null, still return puc/co/note (never 5xx). Also add `GET /empower?lat&lon` only if the frontend has no ZIP (reuse the ZIP already resolved for `/zip-insurance`; check `state/place`). Add pytest with a mocked response.

### Frontend: card in Prepare, `medical` tab
New `components/prepare/PowerDependentCard.tsx`, shown in Prepare `medical` tab after `MedicalAccess`, and linked from Home household chips if `medical` has oxygen/dialysis/vent. Content: headline "Do you rely on power for a medical device?"; context chip (ZIP count, only if `available`, with Source and Freshness); 4-step checklist using the existing Checkbox: (1) ask your doctor to certify you for the Texas PUC Critical Care designation, (2) apply with your electric provider (utility), (3) keep backup power and a charged battery for 3 days, (4) register with STEAR / 2-1-1; red box "Never run a generator indoors, in a garage or within 20 ft of windows, doors or vents; use a battery CO alarm. Headache, dizziness, nausea or confusion: get outside and call 911." Honesty line: "Critical care status does not guarantee power or faster restoration." Static fallback text when API fails. All strings in 5 langs (new `i18n-c27.ts` keys `pw.*`). Print/share-friendly not required.

### Knowledge cards (DATA, in data/knowledge/, each with `source:` lines and "Call 911")
1. `power-outage-and-generators.md`: CDC CO rules (outdoors, >20 ft from windows/doors/vents, battery CO alarm), symptoms (headache, dizziness, weakness, upset stomach, vomiting, chest pain, confusion) -> leave, call 911. Source https://www.cdc.gov/carbon-monoxide/about/index.html
2. `power-dependent-medical.md`: emPOWER explanation and limits, PUC Critical Care steps (Subst. Rule 25.497; form URL above), no-guarantee caveat (KHOU/CenterPoint URL from the research), STEAR (tdem.texas.gov/stear), dialysis/CDC lines by reference.
3. `manufactured-homes.md`: "FEMA advises occupants of manufactured housing not to take refuge in the unit during high winds or floods, to evacuate immediately when officials say so, and in a flash flood warning to move to higher ground." Sources https://www.fema.gov/print/pdf/node/695591 and https://www.fema.gov/zh-hans/print/pdf/node/691040. Do NOT cite the Ready.gov Category 5 line. No ACS chip (Census API needs a key).
4. Unhoused (optional, 10 min): append to `special-needs-and-no-car.md` only the 211 sentence (https://www.211texas.org/). Add the "never shelter under bridges or in creek beds" line only after DATA verifies an NWS Turn Around Don't Drown URL.
Frontend (small): manufactured-home 3-line note in the Prepare evacuate tab (`EvacuationHelp.tsx`) with the FEMA link, 5 langs. AI: add a flag in the intent rules so "oxygen / ventilator / generator / mobile home" questions retrieve these cards (BM25 already indexes `data/knowledge/*.md`; just test 3 questions and add 3 lines to `data/eval/questions.jsonl`).

## Bugs and risks spotted by reading code
1. Index-keyed civic i18n (see gotcha): any removal without the `code` change silently mistranslates.
2. `rec.b1` renter copy is duplicated in i18n-extra.ts and i18n-fill.ts (zh, ar twice); one copy is shadowed. Edit both.
3. `docs/sources.md` line 51 and `research-brief.md` line 47 still hold the removed claims; the RAG index also reads research-brief.md, so Ask can repeat "extremely high risk" until the lead edits it. HIGH: lead must fix research-brief.md.
4. data/demo_snapshot/GET__api_civic-*.json (4) and replay snapshots embed old civic text; with DEMO_SNAPSHOT=1 the wrong facts keep showing until re-recorded.
5. `medical.py` supports only `kind=dialysis`; emPOWER is a separate endpoint on purpose.
6. `civic.py` labels bond facts "projects" in the UI while the 181 are bond ID groups; use "project groups" wording (P1-D).
7. Not checked and now removed: auditor-memo figures. If kept, the demo must say "per the county auditor's June 2025 memo".

## Order of work
DATA P1 + BACKEND code-by-fact change (30 min, in parallel) -> FRONTEND P1 i18n (30 min) -> DATA re-record snapshots -> BACKEND `/empower` + FRONTEND card + DATA cards (1 h) -> AI smoke test. Final grep check (P1-D) before 10:30.
