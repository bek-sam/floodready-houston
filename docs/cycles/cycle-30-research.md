# Cycle 30 research: language equity audit (cycles 25-29 screens)

Method: running app, 390x844, en/es/vi/zh/ar, seeded place (Meyerland 29.6876,-95.4583; Addicks 29.7869,-95.644 for Civic), Playwright. Screens: Home (rain card, 5-day chips, gauge "What this level means", NRI chip), Prepare > Medical / Insurance, Drive (parking, `/?demo=1#drive` storm route), Civic (Addicks pool), Home Renting/buying, `/widget?lat=29.6876&lon=-95.4583&lang=es`. /ask not called.
Scripts and screenshots: scratchpad `e2e/c30/` (`{lang}-{screen}.txt/.png`).

Overall: 0 page errors, 0 horizontal overflow, 0 raw i18n keys in any language; `dir=rtl` set for ar; Arabic chevrons, day-chip order and card alignment correct. Safety wording ("Call 911", "Turn around, don't drown", insurance exceptions) is correct in all four languages where translated. The problems are backend strings that bypass i18n.

## Ranked issues

### 1. HIGH. "Where should I park?" result is 100% English in es/vi/zh/ar (including the 911 line)
- Route `#drive`, after "Check this spot". All non-en languages show: "Consider moving your car to higher ground before heavy rain", "Flood records or an active alert flag this spot. Higher ground is not a guarantee of safety.", "This spot is inside the mapped Hurricane Harvey flood extent", and "Based on flood records and maps, not a prediction for this storm. It cannot tell you a spot is safe. Call 911 in an emergency." Only the buttons are translated.
- Source: `backend/app/services/parking.py` L15 (LIMITS), L52-53 (headline/detail), L66 (reason text). UI `frontend/src/components/parking/*.tsx` L66-77 renders `res.headline`, `res.detail`, `r.text` and `res.limits` directly. Cycle 23 added `code` + `t(code)` for other services; parking was missed. Reason items already carry `code` (e.g. "harvey"), but headline/detail/limits have none.
- Fix: return `level` ("move"|"no_flags") plus reason codes/params. Render with `t('p25.park.<level>.h')`, `.d`, `t('p25.park.reason.<code>')` and always `t('p15.park.limits')`, extended with the 911 sentence. The key `p15.park.limits` already exists but is bypassed whenever `res.limits` is set. Do the same for the other reason codes (fema zone, elevation, crossings, alert, no_flags).

### 2. MEDIUM. Widget rain line mixes languages (all non-en)
- Route `/widget?...&lang=es` (also vi, zh, ar). Example: "Pronóstico de lluvia hoy: No excessive rainfall risk expected". `p15.w.outlook` is filled with the backend `day1.label`.
- Source: `backend/app/services/outlook.py` L12; `frontend/src/pages/Widget.tsx` L49 uses `d.outlook?.day1?.label || cat`. Home already localizes this via `outlook.sub.<cat>` (p2.ts L6).
- Fix: in Widget use `t('outlook.sub.'+cat)` (or the Home helper) instead of the label.

### 3. MEDIUM. Arabic: street address in the place chip is bidi-scrambled
- Header chip shows "المنزل · … Blvd 5300" (number moved after the street name; see `ar-outlook.png`). The header and "For: Home · 5300 N Braeswood Blvd" lines are affected whenever a Latin address sits inside RTL text.
- Fix: wrap the address in `<bdi>` or `dir="auto"` / `unicode-bidi: isolate` in the place chip and the "For:" line. Same for gauge names, which are English-only (acceptable proper names, but need isolation).

### 4. MEDIUM. Hardcoded English "Hurricane Harvey" inside translated sentences
- Home exposure chip, from the backend gauge event name: es "Inundación mayor en el medidor más cercano en Hurricane Harvey"; vi "Lũ lớn tại trạm đo gần nhất trong Hurricane Harvey"; zh "Hurricane Harvey期间最近水位站达到严重洪水"; ar "فيضان شديد عند أقرب مقياس في Hurricane Harvey". The same page elsewhere uses "huracán Harvey", "哈维", "هارفي".
- Source: `frontend/src/i18n/p2.ts` L30/L49 (`sum.exp.gauge`, `chip.gaugeHist`) filled with the raw event name. The "Flood history here" list is affected too.
- Fix: map event id (harvey-2017, taxday-2016, imelda-2019, june-2026) to an existing localized event-name key before `fill`.

### 5. MEDIUM. Addicks pool card: units are not localized and are inconsistent
- Civic, Addicks place. The table shows "83.8 ft / 93.0 ft / 96.0 ft / 109.1 ft" in all languages. The sentences use localized units in es ("pies"), zh ("英尺"), ar ("قدم"), but vi uses "ft". Home gauges use localized units (zh 英尺, ar قدم). In ar the unit renders before the number ("ft 93.0") because of the RTL base direction.
- Source: `frontend/src/pages/Civic.tsx` L32 (rows) and the formatter around L33-43, with `p28.pool.*` strings in `frontend/src/i18n/p28.ts`.
- Fix: reuse the Home gauge formatter (localized unit); wrap value+unit in `<bdi dir="ltr">`.

### 6. LOW-MEDIUM. Gauge "What this level means": NWS impact text is English-only
- Home gauge expander, es/vi/zh/ar: "Next impact at 57 ft: Minor flooding begins along Fondren Drive…". The UI discloses it ("Text below is from the National Weather Service (NWS), in English", translated), so this is transparent but not accessible. The Harvey crest line is fully localized.
- Fix (optional): keep the disclosure; consider a one-line translated gloss for the most common impact phrases ("Minor/Moderate/Major flooding begins") or a "Translate with Ask" link. No change needed for correctness.

### 7. LOW. Project and agency names in Civic are English in all languages
- "Corps of Engineers Section 216 Study - Addicks and Barker Reservoirs", "Rehabilitation of Channels Upstream of Addicks Reservoir…", "Harris County Housing and Community Development", and so on. Intended (proper names, from data), but the long project titles are also embedded in the translated "Message you can send" letter. The place label "Addicks area" is the seeded test label, not a bug.
- Fix (optional): add short localized gloss after the English project title.

### 8. LOW. Other copy nits
- Insurance countdown (all langs) prints an ISO date "2026-11-30" ("Season ends 2026-11-30" / "Espera de 30 días. La temporada termina el 2026-11-30."). The rest of the sentence uses localized dates. Source: countdown message template; format `season_end` with the locale.
- zh: "洪水季节" (insurance countdown) vs "飓风季" (same card) for the same season.
- ar Medical: "جهاز إنذار للكربون" should read "جهاز إنذار لأول أكسيد الكربون" (CO alarm).
- vi uses "ft" on Home gauges while zh/ar use localized units; "Harvey HWM" in crossing names and "(gulf of Mexico)" (lowercase, data) stay English.
- Drive demo controls (`?demo=1`): sample route labels ("UH campus to Downtown") are English everywhere; demo-only, ignore.
- zh uses ASCII colon in "地点: 家" and "我该把车停在哪里?" (full-width ":" and "？" expected). Cosmetic.
- Tenant letter on `#prepare/renters` ("Tenant letter: repairs after a flood") is intentionally English-only for the Texas landlord. Check that a translated one-line note says so.

## Verified OK (no action)
- Rain-next-24h card, 5-day chips ("No risk" localized, no raw "None"), NRI chip ("Inland flood risk: Relatively Low…"): translated and sensible in all 4 languages.
- Medical power-dependent card (PUC Critical Care, STEAR, 2-1-1, CO box with "call 911"): good in all 4 languages; the ZIP count and caveats are translated.
- Insurance 30-day wait plus exceptions (mortgage, renewal changes): accurate in all 4 languages; the "NO flood coverage" warning is retained.
- Storm demo verdict: "Turn around, don't drown. Call 911 if you are in danger." is translated in es/vi/zh/ar. The hazard list embeds English street names (proper nouns).
- Tenant relocation card (p28.ten.*): translated in all languages (JSON labelled "AI-reviewed, pending native-speaker review").
- Addicks pool narrative and datum caveat: translated.
