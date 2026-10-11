# Cycle 33 plan — after-flood recovery (from cycle-33-research.md)
Skip: contractor-fraud (source 402, unverified), CDC food/tetanus numbers (pages not loaded), "24-48 h" mold drying, any hardcoded FEMA IA deadline.

## A. FEMA declaration status — BACKEND
GET `/declarations?county=Harris&state=TX` (OpenFEMA DisasterDeclarationsSummaries v2, no key, cache 6 h, 200 + available:false on failure) →
`{available, county, state, latest:{disaster_number, title, incident_type, declaration_date, incident_begin, incident_end|null, ia_program:bool, ha_program:bool, url}|null, active_ia:bool, recent:[same shape, ≤5, newest first], source, note, meta}`
- `active_ia` = latest declaration with ia_program true AND (incident_end null or ≤ 60 days before today) — note string explains "FEMA's page lists the registration deadline per disaster".
- `url` = https://www.fema.gov/disaster/{disaster_number}. Tests with mocked fetch.

## B. Recovery UI — FRONTEND (After a flood page)
- Banner from /declarations: active_ia → "Federal disaster declared: DR-n — apply at DisasterAssistance.gov" (link); else neutral "No active federal individual-assistance declaration for Harris County (latest: DR-4798 Beryl, Jul 2024). If one is declared, apply at DisasterAssistance.gov." Never invent deadlines.
- NFIP proof-of-loss date calculator in RecoveryTracker: input date of loss → "Proof of loss generally due within 60 days: <date>" + fema.gov link (exact URL from research doc).
- SBA disaster loans card: homes up to $500,000, personal property (incl. renters) up to $100,000 — only when a declaration exists those loans are available; link sba.gov.
- EPA mold steps (from the verified EPA page; no hour figures) and Houston heavy-trash note + "call 311".
- Strings in src/i18n/p33.ts, 5 languages, every fact with its source link.

## C. DATA — knowledge cards for the Ask assistant: fema-aid-and-declarations.md, nfip-claims-proof-of-loss.md, sba-disaster-loans.md, mold-cleanup.md (verified URLs only).
