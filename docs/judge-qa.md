# FloodReady: judge Q&A prep

Answers are grounded in the code (file:function so you can open it live). Keep each under 20 seconds. Say the limitations first (section 2).

## 0. How it works, in 5 lines (memorize)
1. You type an address; we geocode it and combine FEMA's flood zone, the City's Harvey flooded/not data, elevation and live river gauges into one plain-language risk card.
2. "Drive Safe" gets a real road route, checks it against 128 known flood-prone crossings and community reports, and says safe, caution or avoid.
3. "Avoid" only happens when the route crosses a high-risk spot AND flooding is active now (NWS flood alert, a gauge in flood stage, or a deep report).
4. Ask FloodReady is a LangGraph agent: classify the question, search our sourced knowledge cards, call our own tools (risk, routes, claims), then answer with citations in your language.
5. Every feature has a no-key fallback and the app is an installable offline-capable PWA, so the demo can't crash on a missing key or a dead Wi-Fi.

## 1. The 25 toughest questions

### Technology
**1. How does the route check decide "avoid"?**
`services/route.py:check_route`. Get an OSRM route, find crossings within 75 m of it (`BUFFER_M`) and community reports within 100 m. "Avoid" = at least one hazard rated high AND conditions active (NWS flood alert, gauge at action stage or higher, simulated storm, or a report 6 in or deeper). Hazards without active conditions give "caution".

**2. What if routing fails or the route is wrong?**
It never says "safe". In `check_route`, if OSRM fails we draw a straight line and return "caution: Route unavailable, check manually" with a warning. OSRM's public demo server is a risk; routes are disk-cached (`diskcache`) and the four demo routes are pre-seeded in `DEMO_ROUTES`.

**3. Why LangGraph instead of one prompt?**
`ai/graph.py:build_graph`: classify_intent, retrieve, agent, answer_with_citations. A single prompt can't call live tools or guarantee citations. Splitting steps lets us run the same pipeline with no Gemini key (rule-based intent, BM25, templates) and filter citations in code. Honest note: it's a linear graph, not a complex multi-agent loop.

**4. What if the AI hallucinates?**
Three guards. The model only sees retrieved cards and tool results. `answer_with_citations` keeps only URLs that were actually retrieved or returned by tools. If Gemini errors, `agent` falls back to templates built from sourced text. Emergencies always say "Call 911", and every answer says "not official guidance". We can't guarantee zero hallucination; we constrain it.

**5. How does RAG work here?**
`ai/rag.py`: markdown in `data/knowledge/`, `research-brief.md` and `flood-problems.md` is chunked by heading, each chunk keeps its source URL. `Index.search` ranks with BM25 always, and adds Gemini embeddings (`gemini-embedding-001`) when a key exists. With Postgres it can use pgvector; otherwise numpy in memory.

**6. How do you know the Harvey data is accurate?**
We don't claim it's perfect. `harvey.py` uses the City of Houston's own Harvey inundation estimate (357,241 polygons in a SQLite R*Tree, 11-21 ms lookups; riverine only, source URL in the file), point-in-polygon. Outside the City of Houston coverage it returns "no Harvey extent data", never "not flooded". A "not flooded" result is worded "not proof it stayed dry" because street flooding and many floodplain-outside homes are missing. It's a labeled estimate, not a determination.

**7. What happens offline?**
`frontend/public/sw.js`: shell is precached and served network-first, so a reload offline still opens the app. Replay, civic, insurance countdown, demo routes, shelters and outlook are stale-while-revalidate. Offline only shows data you already loaded; live gauges, alerts and fresh route checks need a connection. Not a full offline mode.

**8. How does Watch/push decide to alert?**
`services/watch.py:evaluate` scores a place ok/watch/warning from NWS flood alerts, nearby gauge stage, crossings within 1 km and recent road reports. A 5-minute background loop pushes only when the level rises. It uses standard Web Push (VAPID), so iOS needs 16.4+ and install to Home Screen.

**9. Why should we believe "33 of 52 problems"?**
Because we tried to disprove it. On Oct 11 three reviewers checked every problem against the code and ran a live test for each: API calls and phone-size browser runs for real Houston addresses. Their verdict was strict. The app fully solves 5 problems and partly solves 28. It informs on 13. 6 are beyond any app (policy, funding, engineering). That stricter audit lowered our own earlier self-count of 37. Every verdict, test and bug is in `docs/problems/` (verify-AB/CD/EFG.md), and the bugs it found were fixed the same morning.

### Design and completion
**10. Who is this for, and how did you test with real users?**
Houston residents, especially renters, non-English speakers and drivers. Honest answer: no formal user testing in a weekend. We designed from sourced research (`research-brief.md`), made the address the entry point, and added five languages. Next step is testing with community groups.

**11. Is it finished? What's stubbed?**
End to end working: risk, history, claims, route check, replay, Watch/push, Ask, Prepare, Recover. `scripts/demo_check.py` runs 21 checks. Not done: native app, background location, live Twilio SMS (simulator only). Shelters are historical data, not live. 375px phone layout was not verified visually; check on a real phone.

**12. Accessibility and language?**
UI is translated to Spanish, Vietnamese, Chinese and Arabic: 1,338 strings x 5 languages, 0 missing (`scripts/i18n_coverage.mjs`), backend messages carry codes rendered in each language. Voice alerts in those languages, WCAG AA contrast, easy-read mode. Caveat: translations are AI-reviewed, pending native-speaker review, and some source cards and proper names stay in English.

### Learning
**13. How much did you build vs AI?**
Honest answer: Claude Code wrote much of the code via parallel agents, each owning a folder; disclosed in README. My part: choosing the problem, the 52-problem research, product decisions, data choices, checking results, and fixing what agents got wrong (for example the "Open" shelters label and the 77% stat dates). I can explain every file shown.

**14. What did you learn / what went wrong?**
Hyperlocal risk beats generic data. Concrete misses we caught: shelter data was 2017 but shown as "Open"; any Severe alert wrongly raised "warning"; the 77% stat is Texas 1959-2008, not later. Lesson: verify every number and always build fallbacks (CHANGELOG cycles 1, 4).

**15. What was the hardest technical problem?**
Unreliable public APIs. The live TranStar sensor feed is 403, FEMA/Houston ArcGIS are slow, and USGS is retiring its old service. We used the new USGS OGC API, caching (`diskcache`), pre-extracted Harvey polygons offline, and an elevation fallback.

### Pitch and business
**16. Business model?**
Honest: not built, hackathon scope. Plausible: free for residents; paid for landlords, property managers, insurers and employers who want watchlists and route alerts for sites and fleets; grants or city/county partnerships. Free public data keeps cost low (~1 GB VPS).

**17. Why not just use Google Maps / FEMA map / existing apps?**
Those show a road or a map zone. FloodReady puts FEMA zone next to "flooded in Harvey", and ties routes to Houston-specific flood-prone crossings and live gauges. Half of Harvey-flooded homes were outside mapped floodplains, which a FEMA lookup alone misses.

**18. What's the real-world impact?**
77% of Texas flood deaths (1959-2008) were driving into water, so a clear "avoid this route" before you leave is the highest-value feature. We haven't measured outcomes; impact today is a prototype plus a sourced problem map.

### Environment and Immersive
**19. Environmental angle?**
Climate-driven flooding and aging 2007 maps: FEMA's draft maps use 30%+ higher rainfall rates. We make that hidden risk visible per address, show buyouts and the flood-bond tracker, and flag renter/buyer risk using real NFIP claims by ZIP.

**20. What is "immersive" about it?**
Storm Replay: real USGS gauge history for Harvey, Tax Day, Imelda and June 2026, a water-level tube, a timeline slider, and Narrate speaking at flood-stage crossings. There is also a 3D replay (MapLibre + OpenFreeMap buildings, illustrative rising water from real gauges); it is not VR.

### Voice, resilience, freshness, localization, privacy
**26. How fast is Voice mode and how did you pick the model?**
End of speech to first audio is 0.64 s on a follow-up, 1.0 s in English and 1.4 s in Spanish in the fake-mic E2E (CHANGELOG, Voice v2). `scripts/bench_live.py` compared Live models, 3 sessions each: `gemini-3.1-flash-live-preview` median 1,424 ms versus 1,681 ms (3.8-live) and 3,828 ms (2.5 native-audio); results in `docs/eval/live-bench.md`. Honest limit: timings use a synthetic `say` voice, and the real-mic loop needs a person (`DEMO-DAY.md`). Context (risk, flood history, ZIP claims, alerts) is preloaded so a spoken answer needs no tool call for common questions.

**27. What happens when the AI quota runs out?**
It did: overnight evals exhausted the Gemini free-tier daily quota for three text models (CHANGELOG, "Citations + quota resilience"). Now a quota-aware key x model rotation marks a 429/404 model exhausted with a retry window (`backend/.cache/quota.json`), tries the next, supports several keys (`GEMINI_API_KEYS`), drops embeddings to BM25 on 429, and finally returns a sourced template answer. The live voice model is a separate quota. Emergencies (street flood) are answered from a canned sourced answer with no model call. `/#status` shows the active model.

**28. How do you handle token cost and speed?**
Deterministic routing (4 of 10 bench answers need no LLM), an answer cache (exact + semantic >= 0.92, location-independent only, never for emergencies), lite vs full model routing, compact tool JSON and adaptive RAG top-k. Bench (`docs/eval/bench-before.json` vs `bench-after.json`): median 811 to 228 ms, 10,229 to 2,973 tokens (-71%), 9 to 5 LLM calls, estimated cost $0.00136 to $0.00039. Quality did not drop: quick eval 40/40, judge eval 18/20 faithful.

**29. How do I know the data is fresh?**
Data endpoints return `meta{as_of, source, freshness, snapshot_date, storm_mode}`; the UI shows Live (<= 15 min), Recent (<= 2 h) or Stale badges, gauges are flagged stale/provisional/spike/offline, and `/#status` lists 12 sources with last success, last error and p50 latency. Static snapshots (dialysis, bond, shelters) carry a snapshot date and `scripts/refresh_snapshots.py` has a dry run. Shelters stay labeled historical. Unused AI services show "Not used yet", not "Healthy".

**30. How complete is the localization?**
`node scripts/i18n_coverage.mjs`: 0 missing of 1,338 strings in en, es, vi, zh and ar. Backend messages return codes that the UI renders in the user's language (`frontend/src/i18n/p12.ts`). Remaining English: proper names and USGS site descriptions. Translations are AI-reviewed and flagged "pending native-speaker review". AI safety eval spans all five languages; zh/ar fall back to an English template body if Gemini is rate-limited.

**31. What about privacy?**
No accounts. Household profile, My place and the neighbor check-in list (names and phones, up to 5) stay on the device; check-in alerts use rounded coordinates, disclosed in 5 languages. Flood-damage photos live in IndexedDB, are never uploaded, and have a delete-all button. Community reports are location-rounded, last 24 h, and wrapped as untrusted text before the AI sees them (prompt-injection defense). SMS is STOP/HELP-compliant and sends nothing without Twilio keys. Push test/simulate reach only the caller's own subscription. Not a legal review; see `docs/business-case.md` risks.

### Sponsors
**21. Gemini: what does it do and what if it's down?**
Plans (`/plan`), the Ask agent's tool calling, and embeddings. `ai/graph.py:agent` catches any Gemini failure and uses the deterministic path (rule intent, BM25, templates), so the app answers either way. Live-key paths are untested if no key was loaded; run `scripts/check_keys.py`.

**22. ElevenLabs: why and fallback?**
Voice alerts in English, Spanish, Vietnamese, Chinese and Arabic matter to people who can't read fast or well in English. `/voice` returns 503 with no key and the frontend falls back to browser speechSynthesis (`ai/voice.py`). Key health: `scripts/check_keys.py`.

**23. Tiger Data: what is actually in it?**
`db.py`: community `reports` and `gauge_readings` become hypertables (`create_hypertable`) when `DATABASE_URL` is Tiger Data Postgres with TimescaleDB, else plain tables/SQLite. A 15-minute poller feeds `/api/gauges/{id}/history` for sparklines. pgvector holds RAG embeddings. Be honest if your Tiger instance isn't connected yet.

**24. Backboard: what does the memory do?**
Stores the household profile (language, mobility, medical, pets, car) so plans and answers are personal. Docs had no memory-specific endpoints, so we write the profile as a message to a Backboard assistant, best effort, and keep the local DB as source of truth (`ai/NOTES.md`, `ai/memory.py`).

**25. Vultr: how is it deployed and secured?**
`deploy/` has Docker Compose + Caddy (auto HTTPS) on a Vultr VPS, setup in ~15 minutes with `deploy.sh`. Security: per-IP rate limits (`/ask` 60/min, `/plan` 40, `/push` 20; raised in cycle 17 because venue judges share one IP), 500-char cap, push only reaches the caller's own subscription (a cycle 4 fix), CORS from `ALLOWED_ORIGINS`, secrets only from `.env`.

## 2. Known limitations: say these before they ask
- **Shelters are historical.** The directory is City of Houston 2017 Harvey data, labeled HISTORICAL and never "open". It is not live shelter status.
- **Crossings come from a limited list.** 128 crossings from a City/KPRC news list, USGS Harvey high-water marks, OSM underpasses and the public TranStar sample, not a complete road-flood inventory. A route with no hit is not proof it's dry; the "safe" text says so.
- **Harvey data is City of Houston only.** 357,241 polygons cover the City of Houston (the coverage bbox is recorded); riverine/inundation estimate only. Elsewhere (Seabrook, Bellaire's own jurisdiction) the app says "No Harvey extent data".
- **No-key answers are templates.** Without Gemini, Ask returns BM25-retrieved, sourced text with rule-based tools. It is correct and cited but less fluent and only covers cue words we wrote.
- **Elevation fallback is approximate.** If USGS EPQS fails, Open-Meteo elevation is used and labeled "approx.". Low-ground only compares against gauges that have a known datum.
- **Live keys:** Gemini and ElevenLabs were verified live (CHANGELOG, "Keys live"); Backboard's API shape and the ElevenLabs Agent engine are unverified. Run `scripts/check_keys.py` before judging.
- **Routing relies on the OSRM public demo server**, which has no SLA.
- **Offline is partial.** See Q7.
- **Translations are AI-reviewed, not native-reviewed** (vi/zh/ar headers say so), and no formal user testing was done.
- **Gemini free-tier quota is shared and was exhausted once overnight**; rotation and fallbacks exist (Q27), and zh/ar can fall back to an English template body when rate-limited.
- **SMS is a simulator** unless `TWILIO_*` is configured; no real messages are sent.
- **The 33/52 count is a self-audit**, and not official guidance anywhere: in danger, call 911.
