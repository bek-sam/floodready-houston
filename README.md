# FloodReady Houston

An address-first flood safety app for Houston, built for **CodeRED Orion (UH)**. It follows a person through the flood lifecycle: **Know, Prepare, Drive and Alert, Recover, Hold accountable.** It addresses the 52 Houston flood problems catalogued in [`flood-problems.md`](flood-problems.md); the feature-to-problem mapping is in [`app-plan.md`](app-plan.md).

Not official guidance. In an emergency, **call 911**.

## Features mapped to problems
| Module | What it does | Problem IDs |
|---|---|---|
| Know your risk | Address lookup shows the FEMA zone next to "flooded in Harvey" (Harvey inundation data), elevation (Open-Meteo fallback, labeled approx.), low-ground flag, nearby gauges, reservoir area, jurisdiction, WPC Day-1 rain outlook badge | B1-B9, B11, F2 |
| Flood history here | Per-address history: Harvey flooded or not, Tax Day / Harvey / Imelda / June 2026 peaks at the nearest gauge, ZIP peak claims year | E4, G6 |
| Renting or buying here? | OpenFEMA NFIP claims by ZIP (77096 Meyerland: 6,482 claims, 2,610 since 2017), claims-by-year chart, landlord/seller checklist | E1-E3 |
| Storm replay + Narrate | Replay Harvey, Tax Day, Imelda, June 2026 with real USGS gauge history, water-level tube, timeline slider; Narrate speaks at flood-stage crossings | B7, B10, D4, G6 |
| Gauge history | 48h sparklines from a Tiger Data-ready time series (`gauge_readings` hypertable, 15-min poller, `/api/gauges/{id}/history`) | D4 |
| Prepare | 30-day insurance countdown + .ics reminder, household profile (Backboard memory), Gemini-built plan, special-needs card (STEAR, 211/311), dialysis finder (117 Harris County CMS facilities, tap to call) | C1-C6, E1-E3, D2 |
| Drive Safe | Flood-prone crossing map, "before you drive" route check (safe / caution / avoid; never "safe" if routing fails), community reports count as hazards, simulate-storm demo mode | A1-A9 |
| Live alerts | Watch places (NWS alerts + gauges + crossings + road-flood reports), PWA Web Push, ElevenLabs voice in EN/ES/VI/ZH/AR | D1-D7, G3 |
| Recover | Historical (Harvey 2017) shelter directory labeled HISTORICAL, buyout navigator, post-flood money safety and mold, FEMA aid steps, recovery tracker, share-location-for-911 card, community reports | G1-G5 |
| Hold accountable | Reservoir and dam explainer, flood-bond tracker, who is responsible | F1-F7 |
| Ask FloodReady | Cited assistant in the user's language: deterministic routing, answer cache, per-sentence [n] citations, tools for risk, alerts, routes, civic, flood history, ZIP claims, dialysis | most |
| Judge page | `/#judge`: QR code plus a 5-step demo checklist | n/a |
| PWA / offline | Installable; network-first service worker, offline cache for risk, routes, shelters, outlook; update toast | n/a |

### Added since the first version (cycles 14-24)
| Module | What it does |
|---|---|
| Voice mode | Full-screen, full-duplex Gemini Live voice (`gemini-3.1-flash-live-preview`): preloaded address context, barge-in, push-to-talk, captions. End of speech to first audio 0.64-1.4 s in the fake-mic E2E; Fast SSE path 0.61 s to first speech (CHANGELOG, `docs/eval/live-bench.md`) |
| Citywide Harvey | 357,241 City of Houston Harvey inundation polygons in a SQLite R*Tree (11-21 ms lookups); outside coverage the app says "no Harvey extent data" instead of "not flooded". 2,093 USGS Harvey high-water marks (`/api/hwm`) |
| Coast and evacuation | Texas evacuation zone + NHC storm-surge depth (`/api/evac`, e.g. Seabrook Zone A), NOAA Galveston tide anomaly and active Gulf storms (`/api/coastal`) |
| 128 crossings | Crossing dataset doubled from 64 (STN high-water marks, KPRC, OSM underpasses); printable underpass warning poster with QR |
| Data freshness | `meta{as_of, source, freshness}` on data endpoints, labeled Live / Recent / Stale badges, `/#status` page for 12 sources |
| SMS channel | Twilio-compatible `/api/sms/inbound` (ALERTS ON/OFF, HELP/AYUDA, STOP) plus a Judge-page simulator; no real sends without `TWILIO_*` |
| Language equity | 1,338 UI strings x 5 languages (en/es/vi/zh/ar), 0 missing (`scripts/i18n_coverage.mjs`); backend messages carry codes rendered in each language; easy-read mode |
| Help and recovery | Neighbor check-in (buddy system, data stays on device), go-bag checklist, pets, 311 card by jurisdiction, flood-damage photo helper (on device, never uploaded), Compare places (`#compare`), storm-season reminders |

Coverage, audited honestly and recounted strictly in cycles 24 and 28 ([`cycle-24`](docs/cycles/cycle-24-coverage.md), [`cycle-28`](docs/cycles/cycle-28-coverage.md)): the app **directly reduces 37 of the 52** problems (71%), informs 13 and leaves 2 unaddressed; the rest are policy problems (details in [`app-plan.md`](app-plan.md)).

Every feature works without API keys (deterministic fallbacks: template text, BM25 search, browser speechSynthesis).

Safety and limits: per-IP rate limits (`/ask` 60/min, `/plan` 40/min, `/push` 20/min by default, overridable via `RATE_*`; raised in cycle 17 because a venue shares one IP), `/ask` capped at 500 characters, push test/simulate reach only the caller's own subscription, CORS from `ALLOWED_ORIGINS`.

## AI: measured efficiency and safety
- **Fewer tokens, faster answers** (10-question live bench, `docs/eval/bench-before.json` vs `bench-after.json`): `/ask` median 811 to 228 ms; prompt + completion tokens 10,229 to 2,973 (-71%); LLM calls 9 to 5; estimated cost $0.00136 to $0.00039. Four of 10 answers need no LLM (deterministic routing); exact + semantic answer cache never serves emergencies; lite vs full model routing.
- **Grounding:** per-sentence [n] citations; unsupported numbers are removed with a warning; community reports are wrapped against prompt injection.
- **Safety eval** (`scripts/eval_ai.py`, `docs/eval/latest.md`): 99-case suite across en/es/vi/zh/ar incl. adversarial, 67% to 87% after fixes; quick suite 40/40 after the efficiency work; citation suite 29/30. Remaining failures are missing expected terms, not dangerous advice or missing 911.
- **Quota resilience:** key x model rotation on 429/404, multi-key `GEMINI_API_KEYS`, BM25-only fallback when embeddings are rate-limited, template answers if all models are exhausted; `/#status` shows the active model.

## Architecture
```
 Phone / browser (React PWA, Leaflet, service worker + Web Push)
        |  HTTPS
        v
 +-----------------+   /api/*    +----------------------------------------+
 | Caddy (auto TLS)|------------>| FastAPI backend (uvicorn :8000)        |
 | static dist/ SPA|             |  routers: risk, alerts, crossings,     |
 +-----------------+             |  route-check, replay, watch, push ...  |
                                 |  ai/: LangGraph agent + RAG (BM25 /    |
                                 |       Gemini embeddings), plan, voice  |
                                 +----+-----------+-----------+-----------+
                                      |           |           |
                  SQLite (volume) or  |   Gemini  |ElevenLabs | Backboard
                  Tiger Data Postgres |           |           | (memory)
                                      v
        Free data: USGS OGC, NOAA NWPS, NWS, FEMA NFHL, USGS EPQS,
        Census geocoder, OSRM, Open-Meteo  + bundled data/ (crossings,
        gauges, Harvey inundation, replay series, knowledge cards)
```

## Local development
Requires Python 3.13 + [uv](https://docs.astral.sh/uv/), Node 20+.
```bash
cp .env.example .env            # optional: keys are not required
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
# new terminal
cd frontend && npm ci && npm run dev    # http://localhost:5173, /api proxied to :8000
cd backend && uv run pytest             # tests
```

## Pre-demo checks
```bash
cd backend && uv run python ../scripts/check_keys.py          # one cheap call per key: OK / MISSING / FAIL (never prints keys)
cd backend && uv run python ../scripts/demo_check.py --front  # 21 automated demo checks, PASS/FAIL in about 4s
```

## Environment variables (`.env`)
| Var | Purpose |
|---|---|
| `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBED_MODEL` | Plans, Ask assistant, embeddings (`.env.example` sets `gemini-3.5-flash`; the demo `.env` runs `gemini-3.1-flash-lite` after the free-tier quota incident; `gemini-2.5-flash` is closed to new users; embeddings `gemini-embedding-001`; `GEMINI_LIVE_MODEL=gemini-3.1-flash-live-preview` for Voice) |
| `ELEVENLABS_API_KEY` | Multilingual voice alerts (otherwise browser speechSynthesis) |
| `BACKBOARD_API_KEY` | Household profile memory (otherwise local DB) |
| `DATABASE_URL` | Tiger Data Postgres, e.g. `postgresql+psycopg://...?sslmode=require`; empty = SQLite |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | Web Push; auto-generated and persisted if unset |
| `MAPBOX_TOKEN` | Optional, only for 3D replay |
| `DOMAIN` | Deploy only: your domain, passed to Caddy (not read from `.env`; set on the deploy command) |

## Deploy (Vultr + domain, ~15 minutes)
1. Create a Vultr Cloud Compute instance (Ubuntu 24.04, 1 GB is enough). Add a DNS **A record** `yourdomain.tld -> VPS IP` (no domain yet? use `1-2-3-4.sslip.io`, which needs no DNS step). Wait until `dig +short yourdomain.tld` returns the IP, otherwise Caddy cannot get a certificate.
2. One-time server setup (Docker, compose, ufw 22/80/443/udp 443):
   `ssh root@IP 'bash -s' < deploy/server-setup.sh`
3. Fill `.env` locally (copy `.env.example`) and set `ALLOWED_ORIGINS=https://yourdomain.tld` (also `VAPID_SUBJECT=mailto:you@example.com`).
4. From the repo root: `VPS=root@IP DOMAIN=yourdomain.tld ./deploy/deploy.sh`
   (builds the frontend, rsyncs the repo incl. `.env`, `frontend/dist` and `data/` with the git-ignored `data/harvey/harvey.sqlite`, runs `docker compose up -d --build`, then curls `/api/health`).
5. Smoke test: `curl https://yourdomain.tld/api/health`, then open the site on a phone. Logs: `ssh root@IP 'cd /opt/floodready/deploy && DOMAIN=yourdomain.tld docker compose logs -f'`.

Tested locally (full stack over Caddy HTTPS, SPA routes, `/sw.js` no-cache, manifest type, `/api/*`, SSE `/api/ask/stream`, WebSocket `/api/live`, restart):
`cd frontend && npm run build && cd ../deploy && DOMAIN=localhost TLS_MODE=internal HTTP_PORT=8088 HTTPS_PORT=8443 docker compose up -d --build`, then `curl -k https://localhost:8443/api/health`; stop with `docker compose down -v`. On the VPS leave `TLS_MODE` unset (automatic Let's Encrypt).

Files: `deploy/Dockerfile.backend` (uvicorn, no `--reload`), `deploy/Caddyfile` (HTTPS, gzip/zstd, security headers + CSP, WebSocket/SSE proxy), `deploy/docker-compose.yml`. SQLite, push keys and caches persist in the `state` Docker volume; Caddy certificates in `caddy_data`.

## Data sources
Full list with endpoints, limits and status: [`docs/sources.md`](docs/sources.md). Main ones:
- USGS OGC API: https://api.waterdata.usgs.gov/ogcapi/v0/
- NOAA National Water Prediction Service: https://api.water.noaa.gov/nwps/v1/
- NWS alerts: https://api.weather.gov
- FEMA National Flood Hazard Layer: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
- USGS EPQS elevation: https://epqs.nationalmap.gov/v1/json
- US Census geocoder: https://geocoding.geo.census.gov/geocoder/
- OSRM routing (demo server): https://router.project-osrm.org
- Open-Meteo: https://open-meteo.com
- City of Houston Harvey inundation (pre-extracted): https://geogimsms.houstontx.gov/arcgis/rest/services/TDO/StormDrainage_Study/MapServer/4
- HCFCD bond data: https://www.hcfcd.org/2018-bond-program/bond-program-project-list
- TranStar flood sensor sample: https://traffic.houstontranstar.org/api/roadwayfloodwarning_sample.json
- Research and statistics with URLs: [`research-brief.md`](research-brief.md), [`flood-problems.md`](flood-problems.md)

## AI tools used (CodeRED disclosure)
- **Claude Code (Anthropic)**: used to plan, write and test much of the code, data pipelines and docs, via parallel agents.
- **Google Gemini**: in-product (trip/household plans, Ask assistant, embeddings for RAG).
- **ElevenLabs**: in-product multilingual text-to-speech for voice alerts.
- **Backboard**: in-product household memory.
- **Lovable**: optional, for early UI drafts (state here if used).
AI answers inside the app are labelled "not official guidance" and cite sources.

## Team and credits
- Team: _TODO: names, roles_
- Built at CodeRED Orion, University of Houston, October 2026.
- Thanks to USGS, NOAA, NWS, FEMA, City of Houston, HCFCD, Rice University researchers, and OpenStreetMap contributors.
