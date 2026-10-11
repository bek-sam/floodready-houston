# Cycle 2 plan (lead) — from cycle-2-research.md Top 6
| Lane | Owner | Items |
|---|---|---|
| A | backend/ (excl. ai) | #4: apply the flood-only alert filter (Flood, Flash Flood, Hurricane, Tropical, Storm Surge, Coastal) in watch evaluation and push payloads; shelter note: remove duplicate 911 and the "((" typo |
| B | data/ | #3: knowledge card `special-needs-and-no-car.md` covering STEAR (State of Texas Emergency Assistance Registry), 211 Texas, METROLift/evacuation transport if sourced, and dialysis (KCER) if sourced — verified URLs only |
| C | backend/app/ai | #1: no-key answers in the user's language (pre-translated fixed sentences for es/vi/zh/ar; English knowledge bullets marked "(English source)"); richer dialysis/no-car/senior steps using card B; #6: fix the plan's "ground-floor-safe" sentence and translate the plan template steps for es (others fall back to en with a note) |
| D | frontend/ | #2: fill the missing vi/zh/ar i18n keys and move hardcoded English in Recover, Watch and Replay into i18n; #5: shelter display cleanup (no duplicate 911, status_2017 label text) |
Acceptance: pytest + AI tests pass; npm run build passes; /api/ask in Spanish returns Spanish lead text; /api/watch/status ignores non-flood alerts.
