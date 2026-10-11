# Houston flood problems: definitions, sources, and what the app really solves

Audit date: Sun Oct 11 2026. Requested by the user: define every problem again, bring up the research sources, review the whole codebase, and test whether the app solves each problem an app can solve.

## Files
| File | What it holds |
|---|---|
| [catalog.md](catalog.md) | All 63 problems (52 original + 11 found during the build), each with a plain definition, evidence with source URLs, and "solvable by an app?". 36 source URLs fetched today (about 29 confirmed). Failed and unverifiable claims are listed at the end. |
| [verify-AB.md](verify-AB.md) | Drivers and flooded roads (A), maps that give false safety (B): code paths, live tests, verdicts, bugs. |
| [verify-CD.md](verify-CD.md) | Insurance (C), warnings that don't reach people (D). |
| [verify-EFG.md](verify-EFG.md) | Vulnerable people (E), infrastructure and governance (F), recovery and rescue (G). |
| [fix-plan.md](fix-plan.md) | Every bug the audit found, assigned and fixed (see "After fixes" below). |

## How each problem was judged
Each verifier read the code path (file:line) and ran a real test against the running app: API calls and Playwright at 390 px for Meyerland, Seabrook, Addicks and Downtown. They checked that the data was right, not just that a screen rendered (for example, that the FEMA zone matches FEMA and the route verdict names real crossings).

- **SOLVES**: a user can act, and the harm is reduced end to end.
- **PARTIAL**: a working feature reduces the harm for some users or situations, with gaps listed.
- **INFORMS ONLY**: correct, sourced information, but nothing the user can act on in the app.
- **NOT APP-SOLVABLE / NOT ADDRESSED**: policy, funding, engineering, or data that does not exist publicly.

## Result for the 52 catalogued problems (strict audit, before fixes)
| Verdict | Count | IDs |
|---|---|---|
| SOLVES | 5 | B1, B2, B3, B6, D7 |
| PARTIAL | 28 | A1, A3–A9, B9, B10, C1, C3, C7, D1–D6, E1–E3, F2, F7, G1–G4 |
| INFORMS ONLY | 13 | A2, B4, B7, B8, B11, C2, C4, C6, E4, E5, F1, F4, G6 |
| NOT APP-SOLVABLE / NOT ADDRESSED | 6 | B5, C5, F3, F5, F6, G5 |

**Honest headline:** the app reduces harm for 33 of 52 problems: it fully solves 5 and partly solves 28. It informs on 13 more. 6 are beyond any app. This stricter audit replaces the earlier self-count of 37 "reduces". That count treated several partial or information-only features as reductions: E4, G5, G6, B7, B11 and A2.

F5 and F6 (flood-bond audit findings) are intentionally not shown in the app. Their dollar figures come from an auditor memo PDF that could not be re-verified, so the cycle-27 fact-check removed them.

## Bugs the audit found (all assigned in fix-plan.md)
- **Route safety:** one anonymous report could flip a route to "avoid", and two anonymous votes could cancel it. A route under an active NWS flood warning could still read as having no known hazards.
- **Parking:** "no flags" inside the Addicks reservoir area. `low_ground` was always null.
- **SMS:** "ALERTS ON" replied "alerts ON" but nothing ever sends SMS. A distress text ("stuck in attic") got no 911 line (fixed first). Address replies always suggested ZIP 77096.
- **Insurance:** ZIP policies-in-force was null for some ZIPs (77586 should be 4,980). The ZIP card needed a ZIP in the place label.
- **Push:** failed sends were never retried. `/watch` accepted places outside Houston.
- **Crossings data:** two bad crossings (x126 label, x119 location).
- **Vulnerable households:** in a warning, households with no car or a medical need were told to "check your route before you drive".
- **Recover:** no electrical, downed-line or floodwater safety guidance.
- **Translation and jurisdiction:** the medical note was English-only in es/ar. Seabrook got Houston copy.

## After fixes (re-verified Oct 11, ~9 AM)
Every bug in fix-plan.md was fixed and re-tested: backend 228 tests pass, the frontend build passes, and i18n is 0 missing in 5 languages.
- **Route:** one community report now gives at most "caution"; "avoid" needs 2 or more reports, or a flood-prone crossing plus active conditions. An NWS flood warning on the route raises "safe" to "caution", and the warning is named.
- **Parking:** Addicks and Barker spots get a reservoir reason ("move" when the pool is at action stage). Browser-checked in Spanish.
- **SMS:** a distress text gets "CALL 911 NOW" plus Ready.gov attic and roof advice first (en/es/vi). "ALERTS ON" now says SMS starts once the service is connected; with Twilio keys it actually sends on a level rise. Replies suggest the texter's own ZIP.
- **Insurance:** ZIP policies in force is fixed (77586 = 4,980, matching OpenFEMA). The ZIP card works without a ZIP in the label.
- **Push:** failed sends are retried, and dead subscriptions are removed. `/watch` rejects places outside Houston.
- **Vulnerable households:** in a warning, no-car and medical households get "Get help to evacuate now" (2-1-1, STEAR, 911). Browser-checked.
- **Recover:** new electrical and floodwater safety card. Browser-checked.
- **Translation and jurisdiction:** the medical note is localized, and Seabrook shows Seabrook contacts.
- **Crossings:** the bogus "gulf of Mexico" source tag was removed. `low_ground` was dropped instead of showing an always-empty value.

The fixes close the listed gaps but do not change any verdict category. The count stays at what was measured.

Recount: 33 REDUCES / 13 INFORMS / 6 NONE of 52

## New problems from the catalogue (not in the 52 count)
After the audit, the screens also cover these catalogue `-new` problems with verified sources: E-new1 power-dependent residents (emPOWER card), E-new3 unhoused people (211 card), G-new3 scams (FEMA fraud hotline), G-new4 FEMA denials (appeal steps), G-new5 floodwater contamination (CDC steps), G-new6 proof-of-loss and SBA. G-new2 (flood-damaged cars) has no verifiable source today, so it stays out of the app.
