# FloodReady Houston: Business Case

*Facts cite repo files (RB = research-brief.md, FP = flood-problems.md, CL = docs/cycles/CHANGELOG.md, EV = docs/eval/latest.md) or URLs. Anything else is labeled "estimate" or "hypothesis". Not official guidance; in an emergency call 911.*

## 1. The problem in numbers
- Harvey flooded **154,170 Harris County homes; only 36% were insured**; about half were outside the 100/500-year floodplains ([Community Impact](https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county)). Statewide: 68 direct deaths, about $125B damage (RB).
- **77% of Texas flood deaths (1959-2008)** were driving into water; Harris County leads the state ([TMC thesis](https://digitalcommons.library.tmc.edu/dissertations/AAI1470211)).
- Insurance gap: about 240,000 NFIP policies for about 1.175M housing units, down from 295,108 in 2022 (RB).
- Maps lag: effective FEMA maps date from 2007; draft maps use rainfall rates 30%+ higher ([source](https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/)). Rice (2026): a shifted Tax Day storm could flood 13,000+ homes over Clear Creek, many outside floodplains ([Rice](https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk)).
- Repeat loss: 869 Severe Repetitive Loss properties, $400M NFIP claims in Harris County outside Houston (RB).
- Renters: more than 475,000 Harris County residents live in at-risk multifamily housing ([Planetizen](https://planetizen.com/node/103514)).

## 2. Who is hurt, and their job-to-be-done
| Segment | Evidence | Job to be done |
|---|---|---|
| Renters | Nobody told them it floods; no city/county disclosure requirement (FP B9) | "Tell me before I sign if this place floods, and what to ask the landlord." |
| Limited-English households | AlertHouston is English/Spanish only; state data hard to read, not in Spanish (RB) | "Warn me in my language, out loud." |
| Caregivers, dialysis and older adults | 4 Harvey deaths from lack of medical care; 56% of victims over 50 (FP E1, E2) | "Is my route to dialysis open, and what is my plan?" |
| Drivers | 77% stat above; 81% of Harvey deaths were drownings, many in vehicles (FP A8) | "Is my route safe right now?" |
| Homeowners | Half of flooded homes outside mapped zones; 30-day NFIP wait (CL cycle 11) | "Should I insure, and do it before the wait costs me." |

## 3. Solution and why now
FloodReady is an address-first PWA: FEMA zone beside "flooded in Harvey", ZIP-level NFIP claims, route check (safe / caution / avoid), storm replay, Watch with Web Push and SMS, tenant-disclosure letter (Tex. Prop. Code 92.0135), dialysis finder, and a cited assistant. Voice runs in **5 languages** (EN/ES/VI/ZH/AR). Self-audit: it **directly reduces 36 of 52 catalogued problems (69%)**, informs 14, 2 are not addressed; the rest are policy issues (strict recount in `docs/cycles/cycle-24-coverage.md` + `cycle-28-coverage.md`; self-audit, not a measurement).

Measured (CL cycles 18-19, EV):
- Live voice model benchmark: median 1.42 s (gemini-3.1-flash-live-preview), versus 3.83 s for the slowest option tested.
- 10-question bench: median 811 ms to 228 ms; tokens 10,229 to 2,973 (-71%); est. cost per run $0.00136 to $0.00039 (`docs/eval/bench-*.json`).
- Voice: end of speech to first audio 0.64-1.4 s (CHANGELOG, Voice v2).
- Citywide Harvey lookup (357,241 polygons): 11-21 ms. Cache prewarm: 30.8 s to 0.5 s.
- AI safety eval: quick suite **40/40**; full 99-case suite (5 languages, adversarial included) 87% after fixes, with remaining failures being missing expected terms, not dangerous advice or missing 911 (CL cycle 19).

**Why now:** new FEMA draft maps and Rice's hidden-risk modeling are in the news (2026); BRIC is in legal limbo (section 5); 2026 data APIs (USGS OGC, NWS, OpenFEMA) are free and mature, so unit cost is small (a 1 GB VPS per judge-qa Q16).

## 4. Differentiation (honest)
| Capability | FloodReady | ReadyHarris | Harris Co. FWS | FEMA maps | First Street | TranStar | AlertHouston |
|---|---|---|---|---|---|---|---|
| Address-level risk | Yes | No (general advice) | No (gauges) | Zone only | Yes (score) | No | No |
| "Flooded in Harvey" next to zone | Yes (citywide) | No | No | No | No | No | No |
| Live route verdict | Yes (limited to 128 known crossings) | No | No | No | No | Sensors only, no rerouting | No |
| Real-time alerts | Yes (Push, SMS) | Yes | Gauge map; "not a notification system" | No | Static | Sensors | Yes |
| Languages | 5 incl. voice | 5 (alerts) | Limited | EN | EN | EN | EN/ES |
| Renter/buyer tools | Yes | No | No | No | Partial | No | No |
| Official, authoritative | **No** | **Yes** | **Yes** | **Yes** | Commercial model | **Yes** | **Yes** |
Sources: RB 1.5, FP D1, D5. First Street and FEMA cells are from RB; ReadyHarris "alerts in 5 languages" is from RB, and FP D5 says accessible formats exist only in EN/ES. Weaknesses: we are not an official source, crossings data is limited, and the live TranStar feed is not public (FP D6). Positioning: **a layer on top of official tools, not a replacement.**

## 5. Users, buyers, business model
Residents pay nothing. Revenue comes from institutions that already have the problem. All prices are **hypotheses** to test in the pilot.
| Buyer | Offer | Price hypothesis |
|---|---|---|
| City/County emergency management | Multilingual address-level layer, SMS channel, report dashboard | Annual license, pilot $0-25k |
| Property managers | Tenant flood-disclosure workflow (Tex. Prop. Code 92.0135), resident alerts | Per-unit per month, cents-level |
| Health / dialysis outreach | Patient route and plan outreach, consent-based | Per-site subscription |
| Grants | Mitigation and recovery funds (below) | One-time |
| API | Risk and history endpoints for apps and insurers | Usage tiers; **no sale of resident data, ever** |

Grant status (verified Oct 2026):
- **FEMA BRIC:** a federal judge ruled in Dec 2025 that its termination was unlawful and ordered enforcement in March 2026; FEMA says a new funding opportunity is coming; no award timetable ([CRS](https://www.everycrsreport.com/reports/IN12609.html)). Treat as uncertain.
- **FEMA FMA:** not cancelled with BRIC but no active FY2026 NOFO found (single secondary source; confirm on fema.gov).
- **HUD CDBG-DR:** 2024 disaster allocations went to the City of Houston ($314.6M) and Harris County ($67.3M); action-plan status unverified ([Texas GLO](https://glo.texas.gov/sites/default/files/documents/disaster-recovery/2024-disasters-one-pager_update_4-23-25.pdf)). Harvey-era Harris County spending was slow (HUD OIG: 112 of 4,513 planned participants served at year 3), so funds exist but the pipeline is slow; plan for partnerships, not dependence.
- Local philanthropy: to be identified (no sourced program yet).

## 6. Impact model
**KPIs:** weekly active watchers; share of non-English users; insurance reminders set; tenant letters generated; route checks resulting in "avoid"; eval pass rate (target 100% on emergencies); median latency.

**Illustrative calculation (estimate, not a result).** Formula: policies bought early = N x reach x conversion.
- N = 475,000 Harris County residents in at-risk multifamily housing (sourced above).
- Assumed reach = 5% (hypothesis); assumed conversion = 10% of those reached buy or ask for coverage (hypothesis).
- 475,000 x 0.05 x 0.10 = **about 2,400 people** (estimate).
Why it matters: NFIP has a 30-day wait (CL cycle 11), so a reminder 30+ days ahead converts a storm-day uninsured loss into a covered one; Harvey's insured share was only 36%. Premium context: median $1,501/yr in 77096 (OpenFEMA, n=4,537). We have no outcome data; the pilot measures reach and conversion directly.

## 7. Go-to-market: 90-day pilot
- **Neighborhoods:** Meyerland (6,482 NFIP claims in ZIP 77096, 2,610 since 2017; CL cycle 5), Kashmere Gardens and Alief. Rationale for the latter two is a hypothesis to validate with local data; the app's Harvey data covers the whole city.
- **Partners (verified exist):** BakerRipley, a Houston nonprofit doing disaster case management and neighborhood centers ([Wikipedia](https://en.wikipedia.org/wiki/BakerRipley)); Texas Housers, a low-income housing advocacy group with a disaster-recovery focus ([site](https://texashousers.org)); City of Houston and Harris County emergency management (sign-off needed). None have agreed to anything yet.
- **Channels:** SMS (built), libraries, churches, schools, QR posters at underpasses on known crossings.
- **Days 1-30:** native-speaker review of translations (not done yet), partner onboarding, user tests. **31-60:** live in 3 areas, SMS and posters. **61-90:** measure KPIs, publish results, apply to grants and pitch OEM.
- **Success gate:** 1,000 watchers, 100 tenant letters, zero unsafe AI answers in the monitored sample (targets are hypotheses).

## 8. Risks and mitigations
- **Liability:** labeled "not official guidance", 911 on every emergency answer, never "safe" if routing fails; counsel review before launch.
- **Data licensing/reliability:** federal data is free; TranStar live feed needs a data agreement; OSRM demo server has no SLA, so move to self-hosted routing.
- **Accuracy:** crossings list is limited (128) and Harvey data is riverine only and City of Houston only; the UI says "not proof it stayed dry".
- **AI safety:** 99-case eval incl. adversarial; Gemini failure falls back to sourced templates; keep the eval in CI.
- **Privacy:** no resident-data sale; minimal PII; SMS consent (STOP/HELP built).
- **Sustainability:** low hosting cost; diversified buyers; grant uncertainty shown above.
- **Not yet done:** formal user testing, native translation review (judge-qa Q10, Q12).

## 9. Two-minute pitch and slide headlines
"Harvey flooded 154,170 Harris County homes; nearly half were outside the floodplain and only 36% had insurance. Our tools show gauges and 2007 maps, not you. FloodReady turns your address into a plain-language answer in your language: did it flood here, is my route safe, should I insure. Residents pay nothing. The City, property managers and health networks pay because it cuts calls, disclosure disputes and missed appointments. Our AI passes 40 of 40 safety checks and answers in 228 ms median in the bench. We start with a 90-day pilot in Meyerland, Kashmere Gardens and Alief."
1. Half the flooded homes were never on the map
2. Your address, your language, your route
3. 36 of 52 problems directly reduced, safety-tested
4. Free for residents, paid by institutions
5. 90 days, 3 neighborhoods, measurable outcomes
