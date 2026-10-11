# Cycle 12 research (Sat Oct 10, ~11:30 PM)

Method: read cycle-5 table, cycle-6 and cycle-11 research, the changelog, and the cycle-11 code (WhoToContact.tsx, TenantLetter.tsx, RentBuy.tsx, services/officials.py, buyouts.py, zipinsurance.py, civic.py, tenant_letter_template.md, i18n-c11.ts). Code was read, not run. Problem wording is from flood-problems.md.

## 1. Strict recount

Starting point: 27 REDUCES / 23 INFORMS / 2 NONE (D7, F3).

| # | Was | Now | Why (strict) |
|---|---|---|---|
| A6 | INFORMS | REDUCES | Not a cycle-11 change. Cycle 6 added `barricade_missing` and `water_over_road` report kinds (Recover.tsx KINDS) and routes flag reports within 100 m/24h (services/route.py:86-97). The cycle-6 reason for holding it back no longer applies. |
| B11 | INFORMS | REDUCES | Officials card plus floodplain administrator (name, phone, email, address) from the Floodplain_Administrators layer for the exact point. It tells the user which jurisdiction's rules apply and whom to call. |
| F7 | INFORMS | REDUCES | "Nobody's in charge": the card names the commissioner, the council member (inside Houston) and the floodplain administrator for the point, with tel/mailto links and a copyable message. |
| C1 | INFORMS | REDUCES | Insurance decision block: zone plus ZIP claims plus real premium range plus 30-day wait, which supports a buy/don't-buy decision at the address. |
| C2 | INFORMS | REDUCES | Same block (cost shown, so "uninsured at risk" gets an actionable next step). |
| C6 | INFORMS | borderline | Discloses the typical premium before purchase, but it is a ZIP-wide distribution, not a quote. Not counted below. |
| C4 | INFORMS | INFORMS | No trend or RR2 change is shown, only a snapshot. |
| C5 | INFORMS | INFORMS | No affordability program exists or is linked. |
| B2 | INFORMS | INFORMS | Block shows zone and claims side by side but never states "low-risk zone, still claims". |
| E3 | INFORMS | INFORMS | The letter covers flood-notice and lease-termination rights (§92.0135), not buyout displacement. |
| G1 | INFORMS | INFORMS | Buyout proximity is approximate (point layer) and gives no phone, no timeline help. It answers "who do I call" only weakly. |
| F4, F5, F6 | INFORMS | INFORMS | Policy items. The copyable bond-status message is advocacy, not a fix. |
| A2, A9, B4, B5, B8, D6, E5, F1, F2 | INFORMS | INFORMS | Unchanged. |

**New strict totals: REDUCES 32 / INFORMS 18 / NONE 2 of 52** (62%; 70% excluding the 6 F items: 32/46). If C6 is credited: 33/17/2. Use 32 in the pitch; it survives a judge asking "show me".
The cycle-11 claim of 28 would only hold with C4 plus B2 credited, which the code does not support.

## 2. Code QA of cycle-11 code

No official names are hardcoded anywhere (grepped frontend/src, backend/app, data/*.json, data/knowledge). All names come from layer attributes. Good.

Bugs and gaps, by severity:

1. **ZIP taken from the label can be a house number** (RentBuy.tsx: `label.match(/\b\d{5}\b/g)` and takes the last match). A label like "12345 Main St, Houston, TX" with no ZIP queries ZIP 12345, so wrong claims and premiums appear with no warning. Fix: require the match to follow ", TX", or take the ZIP from the geocoder result.
2. **Insurance block repeats the 30-day wait.** `t('c5.rb.wait')` renders both as a list item inside the decision block and again as a `<p>` at the bottom of the card whenever showDecision is true.
3. **Buyout copy overclaims.** `c11.buyout.in` = "This location is in a buyout area: {name}" fires when the nearest point is up to 0.5 mi away. Say "near" or "within half a mile of". The backend note is correct; the bold headline contradicts it. Same in es.
4. **Premium number is not what a user would pay.** `totalInsurancePremiumOfThePolicy` includes fees and surcharges. The sample mixes all in-force policy types (condo, non-residential, 2-4 family) and any coverage level. `$top=10000` silently truncates large ZIPs with no flag. The UI says "Typical premium: about $1,501 a year" with no caveat. Add "ZIP-wide, all policy types, includes federal fees, not a quote" and the as-of date.
5. **Tenant letter is mangled.** `data/tenant_letter_template.md` has a legal-disclaimer header plus Template A and Template B in one file. TenantLetter renders and copies the whole file, so the user copies both letters. Unfilled placeholders `{phone}`, `{flood_date}`, `{move_out_date}` stay literal because `fill()` has no mapping or inputs for them. The bracketed `[fill in only if true]` also stays. Letter B terminates a lease, so a stray template is risky. Split by heading into a selector, add phone/flood-date/move-out fields (or strip the lines that have no value).
6. **Silent empty states.** WhoToContact returns `null` when there are no officials. A user outside Harris County, or an ArcGIS outage, sees no card and no explanation. Show "No Harris County officials found for this point; call 311 / see hcfcd.org" instead. Buyout failure (`in_buyout_area: null`) also renders nothing; acceptable but unlabelled.
7. **Commissioner precinct is never shown.** officials.py returns `precinct`, but the `Official` type and WhoToContact omit it, so users see "Rodney Ellis" with no "Precinct 1". The floodplain administrator's `entity` ("City of Houston") is also hidden, and that is the key B11 fact. Render both.
8. **Council name casing.** `.title()` turns "MCDONALD" into "Mcdonald" and mishandles suffixes. Use the raw layer value if mixed-case, else title-case with a Mc/Mac exception. Low priority.
9. **officials.py makes 2-3 sequential ArcGIS calls** (precinct, admin, then council). Cold Recover load pays the sum of latencies. Run precinct and admin with `asyncio.gather`, then council.
10. **i18n gaps.** `i18n-c11.ts` has only en and es. vi, zh and ar fall back to English for every new card (tr() falls back to en). The letter body is English only, which is fine since the landlord reads it, but the form labels are untranslated. Say so in judge-qa known limitations, or translate the ~34 keys.
11. **Unsourced or soft numbers.** "Coverage usually starts 30 days" (c11.ins.verdict) has no link in that block; link the existing NFIP source used by c5.rb.wait. The 0.5 mi buyout radius is an arbitrary constant and not disclosed in the UI headline. The 5-mile bond radius in the contact message ("near me") can be a project far from the home.
12. **Cached-failure behaviour.** A failed `_premiums` stores `premiums: None` in the 24 h disk snapshot, so a transient OpenFEMA error hides premiums for a day. Do not persist a snapshot where premiums is None, or retry it.
13. **Tests.** There are no tests for officials, buyouts or premiums (only test_civic_missing_file and zip claims). demo_check.py has no check for /civic officials or /buyout-area.

## 3. Top 4 fixes (each at most 1 h, before the 11 AM freeze)

1. **Tenant letter fix (30-40 min).** Split the template into A and B with a selector, drop the disclaimer line into the card, add phone/flood-date/move-out inputs, and hide Template B's bracketed line. This is the most visible mistake in a demo.
2. **Insurance/buyout copy and correctness (30 min).** Dedupe the 30-day line, soften "in a buyout area" to "near", add the premium caveat and as-of date, and add the NFIP link to the verdict. Include the ZIP-from-label guard (require "TX" before the ZIP).
3. **WhoToContact completeness (30 min).** Show precinct number and the administrator's entity, add the empty-state message instead of `null`, and gather the ArcGIS calls in officials.py.
4. **Tests plus demo_check (45 min).** Mock tests for officials (Houston point returns council, county point does not), buyouts (in/out/None), and premiums (quantiles, empty list). Add `/civic` officials and `/buyout-area` checks to scripts/demo_check.py (Meyerland should return a floodplain administrator). Update COVERAGE_REDUCES in docs/devpost.md and app-plan.md to 32.
