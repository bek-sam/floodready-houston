# Cycle 33 research: after-flood gaps (feature freeze 11 AM; items <= 1h)

Checked 2026-10-11. "Verified" = fact seen on the page by fetch. Several .gov sites (fema.gov, cdc.gov) block curl, so WebFetch was used and some URLs 404.

## What the app has today
- `frontend/src/pages/Recover.tsx`: two checklists (`aid` a1-a4, `buyout` b1-b6), shelters (historical 2017 only), community reports, ClaimsHelper, Report311.
- `frontend/src/components/RecoverExtras.tsx`: RecoveryTracker with 5 items (photos, receipts, FEMA number, claim, mold) and Share911.
- `data/knowledge/fema-aid-and-recovery.md` says outright: "Not covered: grant amounts, deadlines, application steps."
- `post-flood-money-safety.md` covers contractor fraud (TX AG), VIN check, renters, FEMA appeal (60 days from the letter). `post-flood-safety.md` covers a mold card (PMC study, no cleanup steps), electrocution and heat.
- No NFIP proof-of-loss deadline, SBA loans, FEMA declaration status, food/water/tetanus, or debris rules anywhere (grep of claims/, i18n, knowledge returned nothing).

## Live test: OpenFEMA declarations (works, no key)
`https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state eq 'TX' and designatedArea eq 'Harris (County)'&$orderby=declarationDate desc&$top=3&$select=disasterNumber,declarationTitle,declarationDate,incidentType,ihProgramDeclared,iaProgramDeclared,incidentEndDate`
returned HTTP 200 JSON. Newest Harris rows:
- DR-4798 Hurricane Beryl, 2024-07-09, ihProgramDeclared=true.
- DR-4781 Severe storms/flooding, 2024-05-17.
- DR-4586 Winter storms, 2021-02-19.

Meaning: **as of today there is NO federal declaration for the June 2026 flood in Harris County** (only a state declaration, per KPRC in the knowledge base). A checklist that says "apply for FEMA now" would be wrong. Fields: `declarationDate`, `incidentType`, `ihProgramDeclared`, `iaProgramDeclared`, `incidentEndDate`. Note that Beryl shows `ihProgramDeclared` true and `iaProgramDeclared` false, so use `ihProgramDeclared` as the "individuals can apply" flag.

## Gaps (ranked by value / effort)

### 1. FEMA declaration status banner (adaptive aid checklist) - 45 min
- Source: OpenFEMA API above; apply routes: https://www.fema.gov/assistance/individual/program (verified: apply "online, by phone or in person", links to disasterassistance.gov; IHP gives temporary housing/rental help and repair funds, plus "other needs"). That page states NO deadline.
- Helpline 800-621-3362: seen in search results (state/congressional pages), not on a FEMA page we could load. Label it "per state guidance" or omit.
- Deadline caveat: a "60 days from declaration" rule is NOT verified on a FEMA page. Do not hardcode it. Show `declarationDate` and "confirm the deadline at DisasterAssistance.gov".
- Today: a1-a3 of the aid list are generic.
- Add: backend `GET /fema/declaration?county=Harris` (cache 1 h; fall back to "unknown, check DisasterAssistance.gov"). Banner at the top of the aid list. If a declaration is within ~90 days and `ihProgramDeclared`, show "Declared <date>: apply at DisasterAssistance.gov" plus the date. Else show "No federal declaration found for Harris County as of <date>. Document damage now, and SBA/insurance steps still apply."

### 2. NFIP claim + proof of loss, 60 days - 30 min
- Source (verified): https://www.fema.gov/fact-sheet/submit-flood-insurance-proof-loss-form-within-60-days-loss. "submit your Proof of Loss form within 60 days after the date of loss", even if you disagree with the adjuster's estimate. Include the signature, a building damage estimate and a personal-property inventory. A supplemental claim can be filed later. Deadlines can be extended for specific events (FEMA bulletins), so tell the user to ask their insurer.
- NFIP line 877-336-2627 appeared in search output only (unverified on page).
- Today: tracker item "claim" has no date.
- Add: RecoveryTracker date input "date of flood". It shows "Proof of loss due <date+60d>" and the days left. Keeps the 30-day waiting-period logic separate.

### 3. SBA disaster loans (renters + homeowners) - 20 min
- Source (verified): https://www.sba.gov/funding-programs/disaster-assistance/physical-damage-loans. Homeowners up to $500,000 for the primary residence. Renters and homeowners up to $100,000 for personal property (clothing, furniture, cars, appliances). Insurance payouts may be deducted. Loans are for declared disasters (the page says "declared disasters"). Loans are low-interest.
- Today: not mentioned. Renters have no aid path at all besides FEMA.
- Add: one checklist item under `aid`, shown only when a declaration exists (SBA declarations can differ from FEMA ones, so say "if your area is declared").

### 4. Mold cleanup steps - 20 min
- Source (verified): https://www.epa.gov/mold/mold-cleanup-your-home. Under ~10 sq ft (about 3 ft x 3 ft) you can usually do it yourself. Scrub hard surfaces with detergent and water and dry completely. Porous items such as ceiling tiles and carpet "may have to be thrown away". If the area is larger or damage is extensive, consult EPA's larger-area guidance or a professional. The "24-48 hours" figure was NOT found on this page, so do not use it.
- Today: the `post-flood-safety.md` mold card only cites the Houston study. The tracker has a bare "mold" tick.
- Add: 3-bullet "how" under the mold tracker item, with the EPA link. Add the same bullets to `data/knowledge/post-flood-safety.md` (knowledge-owner agent) so Ask can cite them.

### 5. Contractor fraud checklist (strengthen) - 15 min
- Sources: the existing TX AG release (already in knowledge) plus https://www.texasattorneygeneral.gov/news/releases/ag-paxton-issues-consumer-alert-beware-repair-and-clean-scams. That one returned HTTP 402 to WebFetch; the content (licensed/bonded, several estimates, do not sign over insurance checks, get the warranty in writing, report to (800) 621-0508) was only seen in a search summary. Verify in a browser before shipping, or cite just the already-ingested release.
- Today: knowledge card says no full upfront payment and report at (800) 621-0508, but the Recover page doesn't surface it.
- Add: a "Before you hire anyone" item in the aid or tracker list with the 4 bullets and the AG number. Price gouging applies only after a governor's declaration (already in the card).

### 6. Debris pickup, food/water, tetanus - lower confidence
- Debris: https://www.houstontx.gov/solidwaste/heavytrash.html (verified): heavy trash is collected every other month, set out after 6 p.m. the Friday before until 7 a.m. on collection day, just behind the curb (not in the street), max 8 cubic yards per set-out, up to 4 cubic yards of building material, and shingles, brick, plaster and concrete are excluded. The page has NO flood-debris rules, and https://www.houstontx.gov/solidwaste/ says to call 3-1-1 for service issues. Add a short note: "Flood debris: regular heavy-trash limits apply unless the city announces otherwise; call 311." Do not claim special pickup.
- Food/water/tetanus: CDC fetches failed (404/403). Search results only point to old CDC fact sheets: "When in doubt, throw it out", discard food that touched floodwater, perishable food unrefrigerated for 2+ hours, and a doctor decides on a tetanus booster after a puncture or contaminated wound. Not verified on a live page, so **do not ship numbers** until someone checks cdc.gov in a browser. Fallback copy without numbers: "Throw out food that touched floodwater. See a clinician about a tetanus booster after any puncture or dirty wound. Call 911 for emergencies."

## Not recommended
- Hardcoding FEMA grant amounts or a 60-day FEMA registration deadline (unverified; CLAUDE.md forbids invented facts).
- Flooded-car steps beyond the existing VIN card (no new verified source found).

## Suggested order for the next hour
1) NFIP 60-day date calculator (#2, simplest, verified). 2) SBA item + mold bullets (#3, #4, static text with links). 3) FEMA declaration banner (#1, needs a small backend endpoint). 4) Contractor surfacing and the debris note (#5, #6).
All copy needs "Call 911 for emergencies" and "not official guidance"; add i18n keys in the existing en/es/vi/zh/ar files or fall back to English.
