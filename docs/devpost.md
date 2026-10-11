# FloodReady Houston: Devpost submission draft

**Tagline:** Your address, your route, your language: know the real flood risk before the water rises.

## Inspiration
Houston floods, and our tools are built around gauges and 2007 maps, not people.
- Harvey flooded 154,170 Harris County homes, and only 36% of the flooded homes were insured (Community Impact: https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county).
- Nearly half of those homes were outside the 100- and 500-year floodplains (same source).
- 77% of Texas flood deaths (1959-2008) came from driving into water, and Harris County leads the state (https://digitalcommons.library.tmc.edu/dissertations/AAI1470211).
- FEMA's new draft maps use rainfall rates more than 30% higher than the 2007 maps still in effect (https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/).
- Rice researchers (2026) found a Tax Day-size storm shifted a few miles could flood more than 13,000 homes over Clear Creek, many outside official floodplains (https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk).

We catalogued 52 concrete flood problems with sources (`flood-problems.md`) and built one app that covers them.

## What it does
- **Know your risk:** type an address, see the FEMA zone beside "flooded in Harvey", elevation, nearby gauges, reservoir area, jurisdiction and the WPC rain outlook.
- **Flood history here:** Harvey flooded or not, peaks at the nearest gauge for Tax Day, Harvey, Imelda and June 2026, and the ZIP's peak claims year.
- **Renting or buying here?** OpenFEMA NFIP claims by ZIP (Meyerland 77096: 6,482 claims) with a landlord/seller checklist.
- **Drive Safe:** a flood-prone crossing map and a "before you drive" route check that returns safe / caution / avoid; community reports count as hazards.
- **Storm Replay + Narrate:** replay Harvey, Tax Day, Imelda and June 2026 from real USGS gauge history, with voice narration at flood-stage crossings. 48h gauge sparklines come from a Tiger Data time series.
- **Watch and alerts:** save places; get Web Push when risk rises, with voice in English, Spanish, Vietnamese, Chinese and Arabic.
- **Prepare and recover:** 30-day insurance countdown with calendar reminder, personal plan from a household profile, dialysis finder (117 Harris County facilities), special-needs resources, historical Harvey shelter list (clearly labeled historical), buyout, FEMA aid, money-safety and mold guides, recovery tracker, community reports.
- **Hold accountable:** reservoirs, the flood bond tracker, who is responsible.
- **Ask FloodReady:** a cited, multilingual assistant (LangGraph + RAG) that also answers flood-history, ZIP-claims and dialysis questions.
- **Judge page and PWA:** `/#judge` has a QR and 5-step checklist; the installable PWA works offline for risk, routes, shelters and outlook.
- **Hardening:** per-IP rate limits, a 500-character cap on questions, push that only reaches your own device, `scripts/demo_check.py` (21 checks) and `scripts/check_keys.py` (key health).
- Everything works without API keys.

## How we built it
React + Vite + TypeScript + Tailwind + Leaflet PWA with a service worker and Web Push. FastAPI backend (Python 3.13, uv) using USGS OGC, NOAA NWPS, NWS, FEMA NFHL, EPQS, Census, OSRM and Open-Meteo, plus bundled datasets (crossings, Harvey inundation, replay series). AI: Gemini for plans, answers and embeddings; BM25 fallback; ElevenLabs for voice; Backboard for household memory; Tiger Data (Postgres/TimescaleDB) for reports and readings. Deployed with Docker Compose + Caddy (auto HTTPS) on a Vultr VPS under a GoDaddy Registry domain. Built with parallel Claude Code agents, each owning a folder.

## Challenges
- Live roadway sensor feed is restricted (403), so we built our own crossing dataset from the public sample, news lists and research.
- Slow or flaky government APIs (FEMA, Houston ArcGIS): we cache aggressively and pre-extract Harvey inundation offline.
- The legacy USGS service is being retired, so we used the new OGC API.
- Never crashing a demo: every AI feature has a deterministic fallback.
- Keeping every user-facing fact tied to a source and avoiding invented statistics.

## Accomplishments
- Addresses all 52 catalogued problems: the app directly reduces 33 of them (audited Oct 10, cycle 13; the 7 policy problems — dams, flood bond, development, insurance affordability — it makes visible instead), and makes the rest visible (insurance affordability, dam safety and the flood bond are policy problems no app can fix).
- Works end to end with zero API keys.
- Push alerts to a real phone and a storm-simulation mode that makes the demo repeatable.
- A deploy that takes about 15 minutes from a blank VPS.

## What we learned
Flood risk is hyperlocal: a gauge or a map zone does not tell you whether your street or your commute is safe. Plain language, the right language, and a clear "avoid this route" matter more than more data. Sourcing discipline and fallbacks make a hackathon demo robust.

## What's next
- Native app via Capacitor (reliable push, especially on iOS)
- Background location so route warnings arrive without opening the app
- CarPlay / Android Auto turn-by-turn avoidance
- 3D replay, more languages, partnerships with local organizations

## Built with
Python, FastAPI, SQLAlchemy, LangGraph, React, TypeScript, Vite, Tailwind CSS, Leaflet, OpenStreetMap, Web Push / PWA, Gemini, ElevenLabs, Backboard, Tiger Data (TimescaleDB), Vultr, Docker, Caddy, GoDaddy Registry, USGS, NOAA, NWS, FEMA, Claude Code.

## Prize tracks to opt into
- Best Overall
- Best Pitch
- Best Environment Hack
- Most Immersive
- MLH: Gemini
- ElevenLabs
- Tiger Data
- Backboard
- Vultr
- GoDaddy domain
- DEV (publish the write-up with tag `#mlhacks`)

## 2-minute pitch script
**0:00 Hook (15s).** "Harvey flooded 154,170 Harris County homes. Nearly half were outside the floodplain, and only 36% had insurance. Our tools show gauges and 2007 maps, not you. FloodReady is flood safety for your address."

**0:15 Know your risk (30s).** Search a Meyerland address. "FEMA says Zone AE, and here is what really happened: flooded in Harvey." Scroll to Renting or buying: "ZIP 77096 has 6,482 NFIP flood claims."

**0:45 Drive Safe (25s).** Open Drive Safe, choose the Allen Parkway demo route, toggle **Simulate storm**. The verdict flips to **Avoid**. "77% of Texas flood deaths (1959-2008) were driving into water."

**1:10 Replay + Narrate (20s).** Replay Harvey, drag the slider, press **Narrate**: gauges climb through flood stages and the voice calls out each crossing.

**1:30 Ask in Spanish (15s).** Ask "¿Qué hago si mi calle se inunda?" Answer in Spanish with sources and "Llame al 911"; play the voice.

**1:45 Watch push (10s).** In Watch, press **Simulate storm push**; the phone lights up.

**1:55 Close (5s).** "52 problems, one app, 27 directly reduced, works with no keys. FloodReady Houston."

### Demo checklist
1. Phone has the site installed, notifications allowed, subscribed to a watched place.
2. Meyerland address and Allen Parkway demo route tested on the live domain.
3. Keys-unset fallback tested; voice phrases pre-generated.
4. Run `cd backend && uv run python ../scripts/check_keys.py` and `../scripts/demo_check.py --front` (21/21 PASS) before presenting.
