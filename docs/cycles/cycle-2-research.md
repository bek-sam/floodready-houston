# Cycle 2 Research (Sat Oct 10 2026, evening)

Method: curl against :8000/api, code reads of frontend/src and backend/app, two WebSearches (standard). Not opened in a browser. Fetched content treated as data.

## 1. Judge/demo-view issues

- **vi/zh/ar are 29 of 94 keys short** (69 vs 94; es 93). Missing: all `home.*` copy (intro, FEMA plain text, c1-c5, jurisdiction, low-ground), `prep.*` form labels (age, car, medical, mobility, pets, renter, date), `drive.crossings/hazards`, `rec.depth/kind/note`. Falls back to English mid-page. File: frontend/src/i18n.ts.
- **Recover checklists are hardcoded English** (aid, buyout, etc. steps and titles), plus Watch button "Watch this place", Replay toggles "Storm as it fell", empty states ("No shelters listed", "Not available yet"), PushCard messages. Files: frontend/src/pages/Recover.tsx:18-30, Watch.tsx:85, Replay.tsx:117,133, components/PushCard.tsx.
- **Ask in Spanish returns a garbled answer.** Template mode for "¿Dónde puedo ir si no tengo carro...?" gave English bullets starting "- d: restructured Sept 2025 ..." (truncated mid-word) with only a Spanish disclaimer; off-topic bond text, not shelters. Cause: BM25 fallback and chunk truncation in backend/app/ai.
- **Ask (English) dialysis/no-car question is thin**: returns generic medical sentence plus an unrelated "never drive through water" line; nothing about STEAR, 211, dialysis clinic backup. Ask fallback answer quality is the demo risk because no Gemini key (`/api/health` keys all false, db false).
- **Non-flood alerts**: `/api/alerts` returns an Ozone Action Day (severity "Unknown", long raw NWS text). Home.tsx:38-41 already splits flood vs other, so verify in UI that "other" is collapsed; Watch.tsx may not filter.
- **"Normal" hides risk**: `/risk` at downtown gives FEMA X, `low_ground: null` ("Unknown: no gauge datum") and WPC "No excessive rainfall risk" -> screen reads reassuring. Needs wording that "no risk shown today" is not "safe" (see Rice B3 in flood-problems.md).
- **Shelter names/addresses are raw 2017 data**: "George R. Brown Convention Center (City of Houston" (missing paren), "Avanida De Las Americans", status "Full"/"Closed" fields named `status_2017`. Clean in UI. backend/app/routers/shelters.py.
- **Plan steps are English-only** when profile language is vi (template plan returns English titles/details), and one step is garbled: "Move to a ground-floor-safe plan only if it is above flood level" (confusing, possibly unsafe wording). Template in backend/app/ai.
- **Cycle-1 leftovers still open**: shelter banner duplicates "call 911" and has "((" typo.
- **A11y from code**: `<html lang>` is updated and `dir=rtl` set (good), but only ~25 aria/label/alt hits across 12 files and Home.tsx has none; check map markers/charts (StageChart, maps.tsx) have text alternatives; ~17 `text-xs` uses with `text-muted` may fail contrast (verify tokens in index.css).
- **Speech**: speak() falls back to browser TTS with `u.lang` from LANGS; vi/ar voices often absent on judge laptops, so the voice button may be silent without feedback.

## 2. Underserved users: what fails today

- **Spanish/Vietnamese renter, no car**: after the profile form (labels partly English in vi) the plan says "learn the nearest shelter and transit options" but gives no METRO or STEAR info (Recover.tsx:86 does have 211/311, but the plan itself does not). Recover shelter list is 2017 and labeled historical, so there is no live "where do I go". Sources to add: 2-1-1 (dial 211 or 877-541-7905) via https://bellairetx.gov/1914/State-of-Texas-Emergency-Assistance-Regi .
- **Older adult on dialysis**: plan says "ask your clinic" but no STEAR registration (annual, voluntary, includes transport help; Harris County adds registrants to its alert system), no "register before storm" reminder, no dialysis-clinic emergency diet link, no power/backup-clinic checklist item with phone numbers. Source: https://memorialhermann.org/about-us/emergency-information/stear and https://domesticpreparedness.com/articles/evolution-of-a-critical-emergency-response-tool/ . Caveat: confirm current registration URL (sources differ: stear.tdem.texas.gov vs stear.dps.texas.gov).
- **No large-text / simple mode, no phone-call-only path**: seniors without smartphones get nothing; a printable one-page plan (cycle-1 gap, still absent) and "read my plan aloud" in the user's language would help.
- **Route check assumes a car**: Drive has no walking/transit option; "no car" users see "avoid/caution" with nothing to do next.
- **Vietnamese/Chinese Ask answers** are not translated in template mode (disclaimer only).

## 3. New opportunities (free, <=2h)

- **STEAR/211 card** (static, sourced): add to plan for age>=65, mobility, medical, no-car profiles, in all 5 languages; links above. ~45 min. Not previously covered.
- **Apply Home's flood-alert filter to Watch/push messages**: ~20 min, same ozone-noise issue.
- **Harris County FWS gauges**: searched, no public JSON API found (harriscountyfws.org shows maps only; a community scraper exists https://github.com/dcbark01/HouFloodScraper, unverified). Not usable in 2h; keep USGS/NWS.

## Top 6 (by judge-visible impact)

1. Fix Ask fallback: truncated/English answers in es, add a "no car / dialysis" canned answer with 211, STEAR, shelters. (Ask is the most-clicked demo feature.)
2. Fill the 29 missing vi/zh/ar keys and translate Recover checklists, Watch/Replay strings, shelter empty states.
3. Add STEAR + 211 + 311 card to Plan/Recover for seniors, dialysis, no-car profiles (sourced).
4. Apply flood-only alert filter in Watch/push (Home already does).
5. Clean shelter display (missing paren, typos, dup "911", "status_2017" -> "2017 status") and add an explicit "not live" label.
6. Rewrite risky template plan sentence "ground-floor-safe plan" and translate plan steps for the profile language; reword "no risk today" reassurance copy.
