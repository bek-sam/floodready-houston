# Cycle 13 research (Sat Oct 10, ~11:50 PM; freeze Sun 11 AM)

Method: read CHANGELOG, cycle-12 research, TenantLetter.tsx, WhoToContact.tsx, template, i18n key usage (script cross-check of every t('...') literal against i18n*.ts), Recover/Watch/Drive pages. Code read, not run.

## 1. Can any remaining INFORMS/NONE still become REDUCES?

Remaining INFORMS (18): A2, A9, B2, B4, B5, B8, C4, C5, C6, D6, E3, E5, F1, F2, F4, F5, F6, G1. NONE (2): D7, F3.

| Item | Verdict |
|---|---|
| B2 (low-risk zone, still floods) | **Only realistic upgrade.** RentBuy already has zone (c11.ins.zone) and ZIP claims. If zone is X/outside SFHA and ZIP claims > 0, show one line: "Low-risk zone, but this ZIP has N NFIP claims." No new data, about 20 min. Credit as REDUCES only if the line is shown in the demo (33/17/2). |
| C4 (Risk Rating 2.0 trend) | Possible in theory (OpenFEMA policies by policy year), but needs a new query and a check of the premium field. Over 1h to verify. Leave as INFORMS. |
| C6 | Already borderline (ZIP-wide range, not a quote). Leave. |
| C5, A2, A9 | Policy or behavior. A VIN-check link is still INFORMS. Leave as INFORMS. |
| B4, B5 | Map status is a static explainer, no verified free per-address feed. Policy-only, leave as INFORMS. |
| B8 | Needs gauge datum data that is mostly empty. Leave. |
| D6 | No verified free live road-closure feed. Leave. |
| E3, G1 | Buyout displacement and buyout contact need a verified program phone and URA text. Not verified. Policy-only, leave. |
| E5 | Medical finder exists, but closures have no free verified feed. Leave. |
| F1, F2, F4, F5, F6 | Policy-only, leave as INFORMS. |
| D7, F3 | Technical or policy. Leave as NONE. |

Pitch number stays **32 REDUCES** (33 only if B2 is shipped and shown).

## 2. Demo polish sweep

1. **Tenant letter shows raw {landlord_name}, {name}, {address}.** `fill()` in TenantLetter.tsx:
   `map[k] ? map[k] : m` leaves the token when a field is empty. Letter B also shows {flood_date} and {move_out_date} until filled, and `{date}` stays if cleared. This is the most visible issue. Fix: replace empty values with a blank like `________` or `[landlord name]`, and use labelled blanks in the preview. `{phone}` lines are already dropped. (The "[fill in only if true]" marker is stripped. Good.)
2. **Recover report list and map popup print raw `r.kind.replace(/_/g,' ')`** (Recover.tsx:178, 184). "water over road" is an unlocalized English string, not the translated t('c6.kind.' + kind). The saved kind also differs from the KINDS key `stalled_vehicles`, so check the stored value matches. Fix: use t('c6.kind.' + r.kind) with the raw text as fallback.
3. **Hardcoded English in Recover.tsx:178/184/206:** "in", "mi away". Low priority; matters only for Spanish and Vietnamese demos.
4. **Watch.tsx:73 throws a hardcoded English message** ("Flood Watch is not available on the server yet.") if the endpoint 404s. Shown as-is to the user in any language.
5. **i18n keys.** Static t('...') literals: all present. Dynamic keys checked (nav.*, c11.who.*, c6.kind.*, c5.trk.*, home.c1-c5, judge.s1-5, when.*, drive.verdict.*): present for en/es. No raw "home.xyz" key text expected for English or Spanish. Fallback is tr() -> en -> the key itself. The 34 c11 keys exist only in en/es, so vi/zh/ar fall back to English, not to raw keys. Known limitation.
6. **Placeholders substituted by .replace:** all call sites supply their tokens. One risk: if a number is null the site prints "undefined" or "NaN" (e.g. c6.hist.zip uses peak_year, c11.ins.prem uses usd(...)). Guard by hiding the line when the value is null; check these three with a ZIP that has no data.
7. **Console errors likely from code:** clipboard writes are try/caught (ok). localStorage is try/caught (ok). Expected noise: failed tile or ArcGIS requests when offline, the service-worker update toast, and 404s on `/api/watch` if the backend is old. No unguarded `console.*` calls found in frontend/src.
8. Cycle-12 leftovers still open: WhoToContact and RentBuy now have empty states and precinct. Not re-verified: buyout "near" wording and the duplicate 30-day line.

## 3. Top 4 (each at most 1 h)

1. **Letter blanks (20 min), owner `frontend/src/components/TenantLetter.tsx`.** Replace unfilled tokens with `________` (or `[landlord name]`) in the preview, copy and download; disable Copy until landlord, name and address are filled, or show a "fill the blanks" hint.
2. **Localize report kinds and units (25 min), owner `frontend/src/pages/Recover.tsx` (+ `i18n-c5.ts` for "mi away" and "in").** Use t('c6.kind.' + kind) in the popup and list; fix Watch.tsx:73 to use a t() key.
3. **B2 line + null guards (30 min), owner `frontend/src/components/RentBuy.tsx` and `frontend/src/pages/Home.tsx`.** Add the "low-risk zone, still has claims" sentence (+ en/es keys in `i18n-c11.ts`), and hide any {n}/{year}/{med} line whose value is null.
4. **Final doc and check pass (30 min), owner `docs/` + `scripts/`.** Run `scripts/demo_check.py --front`, add `/civic` officials and `/buyout-area` checks, and update COVERAGE_REDUCES in `docs/devpost.md` and `app-plan.md` to 32 (33 if B2 is shown). Add the vi/zh/ar c11 limitation to `docs/judge-qa.md`.
