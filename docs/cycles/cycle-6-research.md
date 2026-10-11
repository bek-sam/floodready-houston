# Cycle 6 research (Sat Oct 10, ~8:45 PM)

## 1. Coverage re-count (strict; checked against code)
Rows changed by cycle 5 (all others unchanged from cycle-5-research.md):

| # | Was | Now | Why |
|---|---|---|---|
| B9 | INFORMS | REDUCES | RentBuy.tsx + /zip-insurance: ZIP claims/policies plus landlord/seller checklist |
| G2 | INFORMS | REDUCES | Share911 card (Recover): location to read to 911 |
| G3 | INFORMS | REDUCES | RecoveryTracker (localStorage checklist: photos, receipts, mold) |
| G4 | INFORMS | REDUCES | Same tracker: FEMA application no., claim filed |
| E5 | NONE | INFORMS | MedicalAccess.tsx dialysis finder (tel: links). No closure or route awareness, so not REDUCES |
| A6 | INFORMS | INFORMS | Reports within 100 m/24h now flag route (services/route.py:86), but there is no barricade report type |
| B2, C1, C2, C4, C6 | INFORMS | INFORMS | ZIP claims data is shown but triggers no action; held back deliberately |
| E4, G6 | INFORMS | INFORMS | "Flood history at this address" timeline was not built |

**New totals: REDUCES 25 / INFORMS 25 / NONE 2 (D7, F3) of 52.** That is 48% REDUCES (25 of 52), or 54% excluding the 6 F policy items (25 of 46). Put 25 in docs/devpost.md COVERAGE_REDUCES.

## 2. Verified facts
(a) 26% over a 30-year mortgage is correct and sourced. The sample lender "Notice of Special Flood Hazards" in federal regulations (e.g. 12 CFR Part 339 Appendix A, fetched and confirmed): "During the life of a 30-year mortgage loan, the risk of a 100-year flood in a special flood hazard area is 26 percent (26%)." Link: https://www.law.cornell.edu/cfr/text/12/part-339/appendix-A. I could not retrieve a FloodSmart page with this wording (floodsmart.gov pages did not return it via curl), so cite the CFR, not FloodSmart. A FEMA flood-map service description also says 1% annual / 26% over 30 years (surfaced by search; not fetched directly).

(b) Elevation fallback works: `curl "https://api.open-meteo.com/v1/elevation?latitude=29.69&longitude=-95.46"` returned `{"elevation":[19.0]}` (metres; about 62 ft). It is free, needs no key, and is a ~90 m DEM (Copernicus), coarser than EPQS. Use it only when EPQS fails, convert m to ft, and label it "approximate".

## 3. Numeric claims with no source link in the UI/backend
Knowledge cards cite sources inline by name (NHESS 2018, ProPublica...) but not as URLs. Concrete gaps:
- frontend/src/i18n.ts:28 "1% ... 26% over 30-year mortgage" (add the CFR link above)
- frontend/src/i18n.ts:43 (and es :89, vi i18n-extra.ts:111) Replay "about 3,600 homes ... above 13,000" has no link beside it (i18n-extra.ts:14 names Rice only)
- frontend/src/i18n-extra.ts:98 (vi) "almost half of Harvey-flooded homes outside 100/500-yr" (en/es equivalents also unlinked)
- backend/app/services/risk.py:60 "154,170 homes, 36% insured" and :62 "more than 30% higher" use SRC_* constants. Confirm these render as links in the Home UI.
- data/knowledge/*.md: every % or count line cites only a name, no URL. Highest risk: insurance-30-day-and-gap.md:8-10, risk-rating-2-premiums.md:5-9, reservoirs-and-dams.md:7-8, flood-zones-vs-reality.md:8-10. The Ask answers only link URLs they retrieved, so confirm the cards carry URLs in their source field.
- i18n-extra.ts:7 "every 2 minutes" is app behaviour, not a claim to source.

## 4. Top 5 remaining (each <=2h, done before the 11 AM freeze)
1. Elevation fallback (Open-Meteo in the risk service, a "from approx. DEM" label). It fixes the "unavailable" gap visible in the demo. About 30 min.
2. Source links for the section 3 items, starting with the 26% CFR link and the Rice replay numbers. It costs nothing and makes the pitch credible. About 45 min.
3. Fill COVERAGE_REDUCES=25 (and the 48% figure) in docs/devpost.md and app-plan.md, then run a demo-script rehearsal on /#judge with the QR pointing at the deployed URL (not localhost). About 30 min.
4. "Flood history at this address" mini-timeline (Harvey polygon hit plus replay events). It moves E4 and G6 to REDUCES, and the "it flooded here" moment is the best demo beat. About 2h; cut to the Harvey-only version if time is short.
5. Add a "barricade missing / water over road" report type and show the count on the route result. It moves A6 to REDUCES. About 1h.
