# FloodReady Houston: App Plan (covers all 52 flood problems)

Problem IDs (A1–G6) refer to `flood-problems.md`.

**Levels of coverage:**
- **REDUCES**: the app directly lowers the risk or closes the gap.
- **INFORMS**: the app makes a problem visible or actionable. These are policy and infrastructure problems that no app can fix.
- **HANDLED**: a technical constraint dealt with in the build itself.

**Planned totals:** 32 REDUCES · 18 INFORMS · 2 HANDLED = 52. **Actual, audited: cycle 5 (8 PM) 21 REDUCES · 28 INFORMS · 3 NONE → cycle 6 (9 PM) 25 REDUCES · 25 INFORMS · 2 NONE → cycle 8 (10 PM) 27 REDUCES · 23 INFORMS · 2 NONE (E4, G6 via flood history) → cycle 12 (11:40 PM) 32 REDUCES · 18 INFORMS · 2 NONE → cycle 13 (midnight) 33 · 17 · 2; remaining 19 are policy-only.** See docs/cycles/cycle-5-research.md; update after each cycle.

The app follows a person through the flood lifecycle: **Know → Prepare → Drive & Alert → Recover → Hold accountable.**

---

## Module 1 — Know Your Real Risk (enter your address)
| Feature | Problems | Level |
|---|---|---|
| FEMA zone shown **next to** "what really happened": Harvey and the 2026 Rice findings, "outside the floodplain ≠ safe" | B1, B2, B3, C7 | REDUCES |
| "Old map vs new rainfall" explainer (2007 maps vs Atlas 14, 30%+ more rain) and a plain-language draft-map status | B4, B5 | REDUCES / INFORMS |
| Mobile-first, color-coded risk card (the draft-map viewer "doesn't work on cell phones") | B6 | REDUCES |
| Low-ground flag from address elevation relative to nearby gauges and drains, a proxy for street ponding and sheet flow | B8 | REDUCES (partial) |
| Renter/buyer disclosure checklist: questions to ask before signing, and whether the address sits in the Addicks/Barker reservoir area | B9, F2 | REDUCES / INFORMS |
| Which jurisdiction's floodplain rules apply to you | B11 | INFORMS |
| Repeat-flood history and support resources | E4 | INFORMS |

## Module 2 — Storm Replay (immersive)
| Feature | Problems | Level |
|---|---|---|
| Replay Harvey, Tax Day, Imelda and June 2026 at your address using **real USGS gauge history** (2D first, 3D stretch), with a timeline slider | B7, B10, D4, G6 | REDUCES |
| "Shift the storm" toggle showing how a few miles changes everything (Rice: 3,600 → 13,000+ homes) | B7 | REDUCES |

## Module 3 — Prepare
| Feature | Problems | Level |
|---|---|---|
| **30-day insurance countdown**: "Buy today and you're covered from <date>"; the uninsured-reality stats | C1, C2, C3 | REDUCES |
| Premium-change explainer (Risk Rating 2.0) and a link to the official FloodSmart estimate | C4, C6 | INFORMS |
| Affordability gap made visible, with an advocacy link | C5 | INFORMS |
| Household profile kept in **Backboard** memory (age, mobility, dialysis/oxygen/medications, car, pets, language) → **Gemini** builds a personal plan ("leave early if dialysis") | E1, E2 | REDUCES |
| Renter rights and buyout displacement explainer | E3 | INFORMS |
| One-tap alert signup with no account validation step | D2 | REDUCES |

## Module 4 — Drive Safe & Live Alerts (the core)
| Feature | Problems | Level |
|---|---|---|
| **Flood-prone crossing map** assembled from TranStar sensor JSON, the KPRC 2026 list and NHESS hotspots ("not adequately delineated or communicated") | A4, A5, A6 | REDUCES |
| **"Before you drive" route check**: the route is checked against alerts, gauges near flood stage, and known crossings → "Avoid Main St underpass" | A1, A2, A7, A8, A9 | REDUCES |
| Personal, timely warnings instead of a generic slogan (TADD shows "no convincing evidence") | A3 | REDUCES |
| Street- and route-level alerts built from NWS county alerts plus gauges and crossings; the county gage map "is not a notification system" | D1, D3 | REDUCES |
| **ElevenLabs voice alerts in 5+ languages** (EN, ES, VI, ZH, AR) with an accessible UI | D5 | REDUCES |
| Live roadway feed is restricted, so use the sample JSON and our own dataset | D6 | HANDLED |
| Use the new USGS OGC API (the legacy API is being shut down in 2027) | D7 | HANDLED |
| Electrocution and floodwater safety voice tips | G3 | REDUCES |
| Hospital, transit and service closure notices | E5 | INFORMS |

## Module 5 — Recover
| Feature | Problems | Level |
|---|---|---|
| Buyout navigator: am I eligible, "Who do I call?", realistic timeline (18+ months) | G1 | REDUCES |
| Post-flood safety checklist (power lines, contamination) | G3 | REDUCES |
| FEMA aid step-by-step and documentation tracker | G4 | INFORMS |
| "I'm safe / I need help" family check-in (911 for emergencies) and the rescue landscape | G2 | INFORMS |
| **Community flood reports** stored as a time series in Tiger Data; optional Solana log for tamper-proof records | G5 | REDUCES |

## Module 6 — Hold Accountable (civic transparency)
| Feature | Problems | Level |
|---|---|---|
| Reservoir and dam risk explainer for your area | F1, F2 | INFORMS |
| Development and paving context | F3 | INFORMS |
| Flood-bond tracker: projects and status near you, audit findings (43 of 181 done, $165M of $834M) | F4, F5, F6 | INFORMS |
| "Who's responsible" — city vs county vs Corps | F7 | INFORMS |

## The long-tail engine — "Ask FloodReady" (Gemini + ElevenLabs voice)
- One assistant grounded in `research-brief.md` and `flood-problems.md`, plus the user's address data and household profile.
- It answers questions on any of the 52 problems in the user's language.
- This one feature covers many of the INFORMS items cheaply.
- Every answer cites its source and says "call 911" for emergencies.

---

## Solo build tiers (~19h)
| Tier | Scope | Time | Problems covered |
|---|---|---|---|
| **1 — Must** | Address risk card (M1), crossing map + route check + live alerts (M4), Ask FloodReady assistant | ~8h | ~35 |
| **2 — Should** | Harvey replay in 2D (M2), voice alerts with ElevenLabs, household plan with Backboard, insurance countdown (M3) | ~5h | +10 |
| **3 — Could** | Recover + Accountable pages (mostly content plus the assistant), community reports in Tiger Data | ~3h | all 52 |
| Stretch | 3D replay, Solana report log | — | — |
| Last 2h | Freeze, rehearse, public repo, Devpost submission covering every track | 2h | — |

## Stack
- Frontend: React + Vite (Lovable optional for the first screens) + Leaflet or Mapbox
- Backend: Node/Express or Python FastAPI on **Vultr**
- Data: **Tiger Data** (gauges, reports, alert log)
- AI: **Gemini** (plans, assistant, route reasoning), **ElevenLabs** (voice, multilingual), **Backboard** (memory)
- Domain: **GoDaddy Registry** · write-up on **DEV**
