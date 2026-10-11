# FloodReady improvement cycles

## Cycle 1 — Sat Oct 10, ~6:30 PM
- Added: /api/shelters (City Harvey-2017 shelter directory, clearly labeled HISTORICAL, never "open"), /api/outlook (WPC Day-1 excessive rainfall badge), post-flood money-safety knowledge card (scams, gouging, flood cars/VIN, FEMA appeals) + mold section, insurance .ics calendar reminder, offline cache for risk/routes/shelters/outlook.
- Fixed: route-check no longer says "safe" when routing fails; Flood Watch no longer escalates any Severe alert to "warning"; stale gauge handling; AI only cites URLs it actually retrieved; vi/zh/ar disclaimers.
- Caught in verify: shelter layer is 2017 data — was showing "Open"; corrected across backend, AI, UI.
- Verified: backend 34 tests, AI 11 tests, frontend build, curl smoke, browser check of Recover.
- Leftover: shelter banner duplicates "call 911" and has "((" typo.
## Cycle 2 — Sat Oct 10, ~7 PM
- Added: special-needs card (STEAR registry, 211/311, dialysis; verified on tdem/211texas/readyharris/CDC); no-key AI answers lead in es/vi/zh/ar; Spanish plan template; 29 missing vi/zh/ar UI keys + Watch/Replay/Recover strings translated.
- Fixed: Flood Watch/push ignore non-flood alerts; shelter banner single 911 + typos; plan "ground-floor-safe" wording.
- Verified: backend 38 tests (incl. AI), frontend build, Spanish /ask returns Spanish lead, browser check of Watch in Vietnamese.
- Leftover → cycle 3: Spanish/other-language cue keywords (carro, diálisis…) so non-English questions get full steps; "Install app" untranslated; home.noRiskToday not wired.
## Cycle 3 — Sat Oct 10, ~7:30 PM
- DEMO FIX: pitch question "¿Qué hago si mi calle se inunda?" (and English) returned nothing/irrelevant → now a sourced multilingual street-flood safety answer (en/es/vi/zh/ar keywords).
- Added: Tiger Data-ready time series (gauge_readings hypertable + 15-min poller + /api/gauges/{id}/history), 48h sparklines on Home, Replay water-level tube + Narrate (voice at flood-stage crossings), /#judge page with QR + 5-step demo checklist, "Install app" translated.
- Verified: backend 41 tests (incl. AI 14), frontend build, history endpoint returns 190 live readings, browser check of Judge and Replay.
- Leftover → cycle 4: tube threshold labels overlap (scale starts at 0 → bunching); QR shows localhost until deployed.
## Cycle 4 — Sat Oct 10, ~8 PM (demo hardening)
- Security: /push/test & /push/simulate only reach the caller's own subscription (was: anyone with the QR could push all phones); per-IP rate limits (/ask 10/min, /push 6/min, /plan 10/min); /ask 500-char cap; CORS from ALLOWED_ORIGINS; uvicorn trusts Caddy's X-Forwarded-For so per-IP limits work behind the proxy (lead fix).
- Reliability: service worker network-first for app shell, build-stamped caches, never returns undefined offline, update-available toast; Watch polling abort/no overlap/reset on simulate toggle.
- Design: StageChart + WaterTube labels readable/de-bunched, axis starts below lowest threshold.
- Facts: 77% stat now "Texas, 1959–2008" (verified on source; 840 deaths is 1959–2009) — fixed in knowledge card + flood-problems.md.
- Verified: backend 44 tests, frontend build, 600-char /ask → 422, simulate without endpoint → 400.
## Cycle 5 — Sat Oct 10, ~8:45 PM (coverage push)
- Honest audit: app REDUCED 21/52 problems (not the 32 planned) → app-plan.md corrected; devpost number pending recount.
- Added: /zip-insurance (OpenFEMA NFIP claims by ZIP; 77096 Meyerland = 6,482 claims, 2,610 since 2017, 4,537 policies in force) + "Renting or buying here?" card with claims-by-year chart + landlord/seller checklist; /medical dialysis finder (117 Harris County CMS facilities) + Prepare card with tel: links; community reports (last 24h, ≤100 m) now count as route hazards; Recover tracker + "share my location for 911" card.
- Verified: backend 48 tests, frontend build, live endpoint values above, browser check of Meyerland address (Harvey flooded banner, Zone AE, renting card + chart).
- Leftover → cycle 6: elevation often "unavailable" (EPQS flaky → add fallback); "26% chance over 30-year mortgage" text needs a cited source; re-count coverage and fill COVERAGE_REDUCES in docs/devpost.md.
## Cycle 6 — Sat Oct 10, ~9:15 PM
- Coverage re-audit: 25 REDUCES / 25 INFORMS / 2 NONE of 52 → filled into docs/devpost.md + app-plan.md (honest pitch number).
- Added: /flood-history + "Flood history here" card (Meyerland: Harvey flooded; Tax Day minor, Harvey major, Imelda action, June 2026 normal at nearest gauge; ZIP peak year 2017 = 2,550 claims); elevation fallback (Open-Meteo, labeled approx.); report kinds (water over road, barricade missing, stalled vehicles) + report count on route; 26% claim sourced to 12 CFR 339 App. A; "nearly half" linked.
- Verified: backend 51 tests, frontend build, live curl of flood-history/risk.
- Leftover → cycle 7: remaining unsourced numbers from cycle-6-research.md §3; AI assistant doesn't use flood-history/zip-insurance/medical tools yet.
## Cycle 7 — Sat Oct 10, ~9:40 PM
- AI: new LangGraph tools get_flood_history / get_zip_insurance / get_medical + en/es intents; e.g. "Did my neighborhood flood before?" (Meyerland) → "This location was inside the area flooded by Hurricane Harvey in 2017 [1]… Brays Bayou… peaked at 45.66 ft (major)."
- Facts: frontend audit found every numeric claim already linked; knowledge card unverified insurance counts (240k policies / Kinder <25%) replaced with verified CSFI figure (lead fix).
- Verified: full backend suite + AI tests pass.
## Cycle 8 — Sat Oct 10, ~10 PM
- Added: scripts/demo_check.py — 21 automated demo checks (PASS/FAIL, ~4s): run `cd backend && uv run python ../scripts/demo_check.py --front` before presenting. Community road-flood reports now raise Flood Watch to "watch". Mobile: tab labels truncate with aria-labels, safe-area padding, overflow-wrap, capped map heights.
- Coverage: E4 + G6 now REDUCES via flood-history → 27/52 (devpost + app-plan updated).
- Verified: demo_check 21/21 PASS, backend 57 tests, frontend build. NOT verified: 375px visually (Chrome window won't shrink below desktop width) — check on a real phone after deploy.
## Cycle 9 — Sat Oct 10, ~10:15 PM
- Added scripts/check_keys.py (OK/MISSING/FAIL per key, never prints values; run after filling .env). README + devpost refreshed for cycles 1–8; pitch rebuilt on verified beats (Meyerland Harvey + Zone AE + 6,482 ZIP claims, Allen Pkwy avoid, Replay Narrate, Spanish street-flood answer, Watch push). "Narrate" button name confirmed in UI by lead.
- Verified: check_keys runs with no keys (all MISSING). Live-key paths untested until user adds keys.
## Cycle 10 — Sat Oct 10, ~10:30 PM
- Added docs/judge-qa.md: 25 code-grounded judge Q&As (file:function to show), known-limitations list, 5-line how-it-works.
## Cycle 11 — Sat Oct 10, ~11:20 PM (informs → actions)
- Added: "Who to contact" (commissioner precinct, council district + phone, floodplain administrator from official layers; copyable message about nearest bond project); insurance decision block with OpenFEMA premium range (77096: median $1,501, IQR $1,007–$2,188, n=4,537) + 30-day wait; buyout-area proximity check (approximate, point layer, no PII); tenant flood-disclosure card (Tex. Prop. Code §92.0135, text checked via texas.public.law mirror — confirm on statutes.capitol.texas.gov) + letter generator.
- Verified: backend 63 tests, demo_check 21/21, frontend build, jurisdiction consistent between /risk and /civic (Bellaire LPA vs City of Houston points).
## Cycle 12 — Sat Oct 10, ~11:45 PM
- Recount: 32 REDUCES / 18 INFORMS / 2 NONE (A6, B11, F7, C1, C2 moved up) → devpost + app-plan updated.
- Fixed: tenant letter now one chosen letter filled from inputs (copy/download/print); ZIP parsed from end of address (was grabbing house number); buyout wording "within 0.5 mi (approximate)"; duplicate 30-day line; premium caveat; WhoToContact empty state.
- Verified: frontend build, demo_check 21/21, browser check of tenant letter. Minor: unfilled fields show {placeholders}.
## Cycle 13 — Sun Oct 11, ~12:05 AM
- Research: only B2 still movable → done (low-risk-zone claims line in RentBuy) → 33/17/2; remaining 19 are policy-only (leave INFORMS).
- Polish: tenant letter blanks show "________", Copy disabled until required fields filled; Recover report kinds + Watch strings translated (en/es).
- Verified: build, demo_check 21/21. Skipped by builder: Home.tsx null guards → cycle 14.
## Cycle 14 — Sun Oct 11, ~12:25 AM (crash-proofing)
- Added ErrorBoundary per page (friendly message + Retry + 911), ~60 null/array guards across pages, api.ts rejects empty/non-JSON bodies.
- Verified: tsc clean, build, demo_check --front 21/21, fresh browser pass over all tabs with 0 console errors (earlier errors were mid-edit HMR).
## Cycle 15 — Sun Oct 11, ~12:50 AM (keyed paths)
- Added backend/tests/test_ai_keyed_paths.py: mocked Gemini (chat + tools + embeddings), ElevenLabs, Backboard (httpx MockTransport).
- Fixed 6 latent bugs that would only appear once keys are added: model-not-found fallback chain; empty Gemini answer / tool-limit with no text → template; /plan code-fence + wrapped JSON parsing; /voice empty audio returned 200 → 503; fabricated URLs stripped; Backboard thread→message flow (Backboard API shape still unverified).
- Verified: 88 tests, demo_check 21/21.
## Cycle 16 — Sun Oct 11, ~1:15 AM (Tiger Data path)
- Tested on local timescale/timescaledb-ha:pg16 (Docker): tables + hypertables (reports, gauge_readings), vector extension, poller wrote 32 readings, reports/watch/push/profile OK, pgvector insert/search OK.
- Fixed: `postgres://` URLs (Tiger Data format) broke AI memory + RAG → shared sqlalchemy_url(); init_db creates timescaledb + vector extensions.
- Verified (lead): demo_check 21/21 against backend on Postgres via postgres:// URL; container removed; SQLite dev server still 21/21.
## Cycle 17 — Sun Oct 11, ~1:45 AM (accessibility + venue-safe limits)
- A11y (WCAG AA): UI border contrast 1.39→3.66:1 (light) / 1.42→4.11:1 (dark); aria-live for Watch level changes, route verdict, alerts, replay level; skip link fixed (was breaking hash routing); slider aria-valuetext; aria-pressed toggles; per-tab document.title; table captions/scope; Drive crossings text list; prefers-reduced-motion + forced-colors.
- Lead fix: rate limits were 10/min per IP — at the venue everyone shares one public IP, so judges could get 429s. Raised to /ask 60, /push 20, /plan 40 per min, overridable via RATE_* env; test now reads limits from config.
- Verified: 88 tests, build, demo_check --front 21/21.
## Cycle 18 — Sun Oct 11, ~2:10 AM (performance)
- Main JS chunk 547 kB → 280 kB (pages lazy-loaded; leaflet + qrcode split); SW precaches hashed chunks.
- scripts/prewarm.py warms every demo address/route/external API cache (first pass 30.8s → second 0.5s); never calls /ask, /plan, /push.
- Verified: build (no chunk warning), demo_check --front 21/21, browser pass of lazy pages with 0 console errors.
## Keys live — Sat Oct 10, ~7 PM (wall clock)
- Gemini key works: default model gemini-2.5-flash is closed to new users → switched to gemini-3.5-flash (.env + .env.example). /ask now generated_by=gemini with real tool calls (get_flood_history, get_risk) and only real source URLs.
- ElevenLabs: key initially lacked text_to_speech permission (401); user fixed it → /voice returns MP3 in en + es. check_keys still reports FAIL for ElevenLabs because it reads subscription (needs optional user_read); TTS itself verified.
- Backend venv was missing uvicorn after agent activity → `uv sync` restored. demo_check 21/21 with live keys.
## Live conversation (Talk mode)
- Frontend: Ask page "🎙 Talk" hands-free loop (Web Speech API listen → /ask mode:voice with last 6 turns → ElevenLabs speak → auto-listen), barge-in, Listening/Thinking/Speaking states with aria-live, auto-stop after 2 silent cycles, unsupported-browser message.
- AI: /ask accepts history + mode:"voice" → returns short `speak` (no URLs/markdown); Gemini emits SPEAK line in the same call; template fallback derives speak.
- Verified with real Gemini: dialysis question → follow-up "what if the power goes out?" resolved via history; advice (STEAR/2-1-1, 3-day medicine supply, CDC 3-Day Emergency Diet) traced to special-needs card (CDC/TDEM sources). 92 tests, demo_check 21/21. NOT verified: live mic loop in browser (needs the user's microphone permission).
## Cycle 19 — regression after keys
- Found: pytest loaded the real .env, so tests called live Gemini/ElevenLabs (slow, spends quota). Fixed in tests/conftest.py (keys blanked before app import). 92 tests in ~16s, no paid calls.
- Fixed: Ask "Send" button wrapping ("Sen/d").
- Browser Talk-mode test blocked: Chrome extension click failures; mic loop needs the user's voice.
- Talk-mode code review: iOS audio unlock on Talk tap (shared Audio element), object URLs revoked, play() rejection → speechSynthesis fallback, single onEnd, 429 ends Talk with friendly message (English only), interim text submitted when no final result, recognizer restarts on language switch. Build passes; mic loop still needs user test.
## Fast voice — Sat Oct 10, ~11:15 PM
- Baseline measured: /ask voice with Gemini tool loop = 26 s; TTS 0.66 s.
- Engine A "Fast" (default): /ask/stream SSE — prefetch tools in parallel, one streaming gemini-3.5-flash-lite call with minimal thinking, per-sentence speak events; /voice/stream (first audio byte 0.33 s), /voice/filler (instant). Measured: "Did my neighborhood flood before?" first speech 0.61 s (Gemini, 4 sources); street-flood emergency questions (en/es) answered instantly from the canned sourced safety answer. QA caught + fixed: street-flood intent skipped, empty sources, English disclaimer in Spanish, missing accents.
- Engine B "Gemini Live (beta)": WebSocket /api/live ↔ gemini-3.8-live native audio, tools via function calling; live round trip first audio ≈1.2 s.
- Engine C "ElevenLabs Agent (beta)": /api/el-agent/signed-url + scripts/create_el_agent.py + @elevenlabs/client UI with client tools — needs user to enable Agents permission and create the agent.
- Fixed: backend hung on reload ("Waiting for background tasks") → lifespan cancels background tasks (clean shutdown ~1 s).
- Verified: 104+ tests, build, demo_check, live timings above. NOT verified: mic-driven browser loops for A/B/C (need the user).
- Typed /ask fixed (was >60 s with real key): reuses fast pipeline (canned street-flood first; prefetch + one minimal-thinking call; LangGraph loop only without location), ASK_TIMEOUT_S=12 hard cap → template + warning, SDK retries off. Live: es street-flood 0.83 s, Harvey 1.0–2.5 s, insurance 0.7 s. 109 tests, demo_check 21/21.
## Professional redesign — Sat Oct 10, ~9:30–11:30 PM
- Design lead spec docs/ux/redesign-spec.md (audit of 11 screens, 5 personas, IA, design system, per-screen specs, demo mode, 6-phase plan). Before/after screenshots in docs/ux/before|after.
- P1 design system (tokens light/dark, Inter, lucide icons, 25 ds components), new shell (5 primary + More, calm 911 strip, My place chip), first-run onboarding with persisted My place (fixes address lost on reload), Demo mode (?demo=1 / Judge toggle).
- P2 Home: summary hero (Right now / This place, rule-based with sourced why-chips + "How we decide"), top-3 personalized actions, live conditions, progressive-disclosure details, trust card.
- P3 Drive/Alerts: My place defaults; simulate + demo routes only in demo mode, "Simulated" label (real users never see a fake Avoid); single alerts switch; ReportSheet.
- P4 Ask: suggested questions, message list with sources/tools chips, voice orb, plain engine names in settings sheet, latency only in demo mode.
- P5 Prepare (fixed wrong "Check my risk" label, household from My place, stepper plan, evacuation help), Judge (QR, steps, demo switch), Recover/Civic split, Replay restyle, honest historical shelters.
- P6 polish: main focus ring removed, header offset, Home grid balanced, 390px first action visible, Judge "Go" wiring, es names, jargon removed, a11y/copy QA. Verified: build, demo_check 21/21, screenshots at 1280 + 390.
## Live talking verified — Sat Oct 10, ~11:55 PM
- E2E fake-mic test (Playwright Chromium, macOS `say` audio as mic): Live (beta) en + es pass — transcript, get_flood_history tool call, spoken reply; first audio ≈4.0–4.5 s after tap incl. ~2 s of spoken question. Standard path verified with stubbed recognition (stream + voice fire).
- Hardened Live: 5 s connect timeout + 1 retry, error/early-close/20 s watchdog → idle with Retry + "Switch to Standard"; echo cancellation + mic muted during playback unless barge-in (RMS 2.5×); interrupted flushes playback; AudioContexts resumed inside the tap (iOS). E2E 3/3 passes.
## Gap-fix round — Sun Oct 11, ~12:30 AM
- Citywide Harvey: all 357,241 City of Houston Harvey inundation polygons in SQLite R*Tree (54 MB, 11–21 ms lookups), coverage bbox recorded; /api/harvey/extent (≤~1 MB GeoJSON); outside coverage → flooded:null.
- Crossings 64 → 128: + USGS STN Harvey high-water marks at crossings (54), re-geocoded KPRC (8), OSM underpasses in Harvey extent (2); documented high/medium rule; "No known flood-prone crossings" wording replaces "safe".
- SMS channel: /api/sms/inbound (Twilio-compatible, signature check when configured), /api/sms/simulate, ALERTS ON/OFF, HELP/AYUDA, STOP; /checkin/script + /checkin/call (503 unless Twilio env). Judge-page SMS simulator in demo mode. No real sends without TWILIO_*.
- Translations: 892/892 keys for es/vi/zh/ar; es 45 / vi 19 / zh 40 / ar 82 fixes; headers "AI-reviewed — pending native-speaker review".
- 3D replay (MapLibre + OpenFreeMap 3D buildings, rising illustrative water from real gauges): built, map canvas renders blank in headless check → being debugged.
- ElevenLabs agent: key lacks convai_write → user must create an unrestricted key.
- 3D replay fixed + verified: root cause maplibre CSS position:relative collapsed the container to 0 px; then water-extent bugs (citywide union polygons tinted the whole view → over-correction hid real flooding) fixed by server-side shapely clip to camera bbox + simplify (≈408 KB / 2 s). Screenshot shows Harvey extent following Brays Bayou (Bellaire/Braeswood/Woodshire) with dry areas and gauge columns. 121 tests.
- AI safety eval: scripts/eval_ai.py + 99 cases (en/es/vi/zh/ar; emergencies, driving, insurance, dialysis, renters, shelters, post-flood, adversarial) × /ask + /ask/stream. Pass 67% → 87% full re-run, 93% quick. Fixed: street-flood false positives (buyout/renter questions), shelter "not live" always stated, non-English retrieval (glossary), "[Live data: none]" leak. Remaining failures = missing expected terms only (no dangerous advice / no missing 911). Known: zh/ar fall back to English template body when Gemini free tier is rate-limited.
## Voice v2 — Sun Oct 11, ~1:30 AM (ChatGPT/Claude-style voice)
- Backend: context preload (risk, history, ZIP claims, alerts, household) into Live system instruction; tuned VAD turn-taking; push-to-talk (manual activity); non-blocking tools + "thinking" events; streaming captions; turn timing events; session resumption + context compression. Live model benchmark → gemini-3.1-flash-live-preview (median 1.42 s vs 3.8-live 1.68 s, 2.5-native-audio 3.83 s).
- Frontend: full-screen VoiceMode, orb reacting to mic + assistant levels, captions, mute, PTT (button/space), true full duplex (echo-mute hack removed, 30 ms flush, 80 ms ring buffer), resume + auto-fallback; "Voice" (Live) is now default.
- E2E (fake mic): end-of-speech → first audio en 1.0 s, es 1.4 s, follow-up 0.64 s; barge-in interrupted+flushed+answered; tool gap 2.3 s with label; PTT 0.7–0.9 s. Fixed: user_end timestamp, PTT stuck in manual mode, tool label timing.
- Demo note: dev --reload drops live sessions → run backend without reload for judging (DEMO-DAY.md updated).
## AI efficiency — Sun Oct 11, ~2 AM
- Deterministic routing (4/10 bench answers need no LLM), answer cache (exact + semantic ≥0.92, location-independent only, never emergencies), model routing (lite vs full), compact tool JSON (≤800 chars), adaptive RAG top-k, /ask/prefetch warming, number-grounding check (unsupported numbers removed + warning), prompt-injection wrapping of community reports, LLM-as-judge eval mode, thumbs feedback (/feedback), telemetry + /ai/stats.
- 10-question live bench: median 811 → 228 ms; LLM calls 9 (+1 timeout) → 5; tokens 10.2k → 3.0k; est. cost $0.00136 → $0.00039. Eval quick 37/40 → 40/40; judge 18/20 faithful. Context caching unavailable on free tier (storage limit 0).
- Lead fix: .env GEMINI_MODEL had been reverted to gemini-2.5-flash (404 for new users) → set to gemini-3.5-flash; config default updated.
## Data freshness — Sun Oct 11, ~2:45 AM
- meta{as_of, source, freshness, snapshot_date, storm_mode} on data endpoints; gauge flags stale/provisional/spike/offline; storm mode TTL 90–180 s; /api/status + #status page (12 sources: health, last success/error, p50 latency; snapshot dates); scripts/refresh_snapshots.py (dry-run: dialysis +20, bond +87, shelters 0); Freshness + GaugeChips UI with labeled badges (Live ≤15 min / Recent ≤2 h / Stale); "Not used yet" instead of Healthy for unused AI services.
- business case: docs/business-case.md (problem, users vs buyers, model, impact model labeled estimate, 90-day pilot, risks, 2-min pitch + 5 slides).
- Verified: 159 tests, build, demo_check 21/21, browser screenshots of Home + Status (no page errors).
## Citations + quota resilience — Sun Oct 11, ~3:15 AM
- Per-sentence [n] citations (citations.py), as-of phrasing for live values; 15 new eval cases 29/30; judge 7/7 faithful before quota ran out.
- INCIDENT: overnight evals exhausted Gemini free-tier daily quota for 3.5-flash-lite / 3.5-flash / flash-lite-latest (reset ~6 PM, after demo). Live voice model unaffected.
- Fix: quota-aware key × model rotation (429/404 → mark exhausted with retry window in backend/.cache/quota.json, try next), GEMINI_API_KEYS multi-key support, embeddings 429 → BM25-only, /api/status shows active model. .env text models → gemini-3.1-flash-lite. Verified live: /ask generated_by=gemini (3.1-flash-lite), 164 tests.
- Policy: no more live-Gemini evals before the demo.
## Deploy readiness + Cycle 20 — Sun Oct 11, ~2:45 AM
- Local git commit 7fc5d6a (358 files, secret-scanned; 52 MB harvey.sqlite git-ignored, rsynced by deploy.sh). NOT pushed (needs user approval).
- Full prod stack tested locally via Docker + Caddy HTTPS: SPA, SW no-cache, SSE /ask/stream, WebSocket /api/live, push, harvey DB in container, no-reload uvicorn, clean restart. Added TLS_MODE, HSTS/nosniff/Referrer/CSP, flush_interval -1, timeouts, body limit; deploy.sh preflight checks + health curl. CSP verified: zero violations incl. 3D replay + Voice.
- Cycle 20 features: /api/evac (Texas evacuation zones + NHC surge; Seabrook Zone A, Cat2–5 surge >3–9 ft), /api/hwm (2,093 USGS Harvey high-water marks; "not your exact address"), /api/coastal (NOAA Galveston tide anomaly +1.4 ft live, NHC active storms), go-bag checklist (print + wallet card; sourced to Ready.gov/CDC, "several days" wording), storm-season .ics reminders. 172 tests, build, browser screenshots, 0 page errors.
- In progress: Harvey coverage limited to City of Houston (no false "not flooded" for other cities); evac zone + surge in Home summary.
- Accuracy: Harvey miss outside City of Houston limits → null "no Harvey extent data" (layer not city-only, hits stay true); verified live: Seabrook null, Meyerland true, Greenspoint true, Downtown false. Evac zone + surge now in Home summary chips/levels. 173 tests, demo_check 21/21.
## Cycle 21 — Sun Oct 11, ~3:30 AM (accuracy audit + pets + posters)
- Fixed (audit): ghost storm "Isaias" over Tennessee shown on Galveston chip → only Gulf/Texas-relevant NHC storms; evac lookup failure showed "not in a zone" → zone_status unavailable + "check ReadyHarris"; 46% of high-water marks were 0 ft (dry) → wet/dry split, depth from nearest wet mark (Seabrook: 5.8 ft at 4.4 mi); surge ranges {min,max,label} "9+ ft"; surge chip paired deepest depth with wrong category (Cat 2+ → Cat 3+, lead fix); .ics RFC 5545 escaping/folding; failed history no longer reads as lower risk; es strings; Home evac disclosure gated by evacShow (lead fix).
- New: Pets tab (Ready.gov-sourced, shelter caveat); printable underpass warning poster with QR to #drive/to=lat,lon.
- Verified: 173 tests, build, browser (Seabrook summary shows Zone A + surge chips, no ghost storm, 0 page errors).
