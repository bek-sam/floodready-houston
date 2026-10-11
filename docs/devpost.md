# FloodReady Houston

**Tagline:** Your address, your route, your language: know the real flood risk before the water rises.

**Code:** https://github.com/bek-sam/floodready-houston

Not official guidance. In an emergency, call 911.

## Inspiration
Houston floods, and our tools are built around gauges and 2007 maps, not people.
- Harvey flooded 154,170 Harris County homes; only 36% of the flooded homes were insured, and nearly half were outside the 100- and 500-year floodplains (Community Impact: https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county).
- 77% of Texas flood deaths (1959-2008) came from driving into water (https://digitalcommons.library.tmc.edu/dissertations/AAI1470211).
- FEMA's draft maps use rainfall rates more than 30% higher than the 2007 maps still in effect (https://reduceflooding.com/2026/02/12/fema-releases-new-draft-flood-maps-for-harris-county-and-houston/).

We catalogued 52 concrete flood problems with sources (`flood-problems.md`) and built one app around them.

## What it does
- **Know your risk:** an address shows the FEMA zone beside "flooded in Harvey" (357,241 citywide polygons), elevation, gauges, reservoir area, evacuation zone and storm-surge depth, flood history, and ZIP NFIP claims.
- **Drive Safe:** 128 flood-prone crossings, a safe / caution / avoid route check (never plain "safe"), community reports with "Still there / Cleared" votes, NWS warning polygons, and a suggested detour with fewer flood-prone spots, always marked "still check conditions".
- **One labelled demo storm:** a single switch drives Home, Alerts and Drive, with a "SIMULATED - demo only" alert and tag, so the demo is repeatable and never passes for real data.
- **Ask FloodReady (agentic):** a cited, multilingual assistant (LangGraph + RAG) with 16 data tools (reservoir pool, FEMA declarations, rain already fallen, neighborhood risk index, power-dependent residents via emPOWER, parking, and more). A "How I answered" trace shows intent, sources searched, live tools with timing, and model or template, at no extra Gemini cost.
- **Voice mode:** full-duplex Gemini Live that already knows your address, with barge-in and captions.
- **After a flood:** FEMA declaration banner (no "apply now" without a declaration), NFIP proof-of-loss date calculator, SBA loans, appeal steps if FEMA says no, scam warnings with the FEMA fraud hotline, floodwater and electrical safety, mold, a "waiting for rescue" card, and a "no home" card (211).
- **Vulnerable households:** dialysis centers show FEMA zone and Harvey flooding (Meyerland: 3 nearest centers in Zone AE, 2 flooded in Harvey); no-car or medical households in a warning get "get help to evacuate now" (2-1-1, STEAR, 911).
- **Works offline:** an offline safety card (911/311/211, last-known zone and elevation, household needs, kit reminders, print) and a fix for a cold offline reload that could blank the app; 11 pages verified offline.
- **Reach everyone:** UI in 5 languages (en, es, vi, zh, ar), SMS channel (simulator), Web Push, PWA, easy-read mode.
- Everything works without API keys.

## How we built it
React + Vite + TypeScript + Tailwind + Leaflet PWA with a service worker and Web Push. FastAPI backend (Python 3.13) over USGS, NOAA, NWS, FEMA, OpenFEMA, EPQS, Census, OSRM and Open-Meteo, plus bundled datasets. AI: Gemini for plans, answers and embeddings, Gemini Live for voice, ElevenLabs for speech; BM25 and templates are the no-key fallback. Integrations ready but switched on only by configuration: Backboard household memory (local DB without a key) and Tiger Data / TimescaleDB hypertables + pgvector (tested on a local TimescaleDB, SQLite by default). Deploy-ready with Docker Compose + Caddy (automatic HTTPS, scripts in `deploy/`) for a Vultr server and a GoDaddy Registry domain. Built with parallel Claude Code agents.

## Challenges
- The live roadway sensor feed is restricted (403), so we built our own crossing dataset from public lists and research.
- Slow government APIs: aggressive caching and offline-extracted Harvey polygons.
- Honest geography: Harvey data covers only the City of Houston, so elsewhere we say "no Harvey extent data" instead of a false "not flooded".
- Gemini free-tier quota ran out overnight, so we built key x model rotation with fallbacks.
- Our own audit caught real bugs (a single report flipping a route to "avoid", Addicks parking showing "no flags", an SMS distress text without 911); all were fixed and re-tested.

## Accomplishments
- A strict, problem-by-problem audit with a live test per problem (`docs/problems/`): the app reduces harm for **33 of 52** problems (fully solves 5, partly solves 28), informs on 13, and 6 are beyond any app. This replaced our earlier, more generous self-count of 37.
- Measured, dated evidence on the in-app Judge page: 240 backend tests passing, AI eval 38/40 (95%), citation eval 15/15 with live Gemini, voice end of speech to first audio median 1.4 s (n=3, small sample), `demo_check` 21/21 online and in offline snapshot mode.
- Accessibility: axe-core 0 violations across 48 combinations (12 views x 2 widths x 2 themes).
- 14-route sweep at 390 px in English and Arabic: 0 errors, 0 overflow, 0 raw keys.

## What we learned
Flood risk is hyperlocal: a gauge or a map zone does not say whether your street or commute is safe. Plain language, the right language, and a clear "avoid this route" matter more than more data. We dropped claims we could not verify rather than ship them.

## What's next
Native app for reliable push, background location for route warnings, live Twilio SMS, native-speaker review of vi/zh/ar, and Harvey-style coverage beyond the City of Houston.

## Built with
Python, FastAPI, LangGraph, Gemini, Gemini Live, ElevenLabs, Backboard, Tiger Data (TimescaleDB), React, TypeScript, Vite, Tailwind CSS, Leaflet, OpenStreetMap, Web Push / PWA, Vultr, Docker, Caddy, GoDaddy Registry, USGS, NOAA, NWS, FEMA, Claude Code.

## Prize tracks to opt into
Best Overall, Best Pitch, Best Environment Hack, Most Immersive, MLH: Gemini, ElevenLabs, Tiger Data, Backboard, Vultr, GoDaddy domain, DEV (`#mlhacks`).
