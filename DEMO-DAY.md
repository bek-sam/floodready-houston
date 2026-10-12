# FloodReady — Demo-day runbook (Sun Oct 11)

Hacking ends **1:00 PM** · judging 1:30–3:30 PM · closing 5 PM.

## Tonight / early morning (only you can do these)
1. **Keys** → `cp .env.example .env`, fill `GEMINI_API_KEY`, `ELEVENLABS_API_KEY` (optional: `DATABASE_URL` from Tiger Data, `BACKBOARD_API_KEY`).
   Check: `cd backend && uv run python ../scripts/check_keys.py` → all OK.
2. **Deploy** (needs Vultr VPS + DNS A-record `yourdomain -> VPS IP`, or use `IP-with-dashes.sslip.io`):
   set `ALLOWED_ORIGINS=https://yourdomain` in `.env`, then
   `ssh root@IP 'bash -s' < deploy/server-setup.sh` and
   `VPS=root@IP DOMAIN=yourdomain ./deploy/deploy.sh` (needs `data/harvey/harvey.sqlite` locally; it prints the health check at the end).
3. **GitHub**: tell Claude "approved — push" (repo must be public for prizes).
4. **Phone push test**: open the deployed URL on your phone → (iPhone: Share → Add to Home Screen → open from Home Screen) → Alerts (`#alerts`) → add a place → turn on "Alerts on this phone" → "Simulate storm alert".

## 30 minutes before judging
```
cd backend
uv run python ../scripts/prewarm.py  BASE   # warm caches (BASE = https://yourdomain or http://localhost:8000)
uv run python ../scripts/demo_check.py BASE --front   # must say 21/21 passed
```
**Open `BASE/?demo=1` first** (or `BASE/#judge` then click the demo button, which also sets demo mode). Demo mode lives in sessionStorage, so it is per tab: after closing the tab, re-open with `?demo=1`. Without it the Drive sample-route chips and "Simulate storm" switch are hidden on purpose (real users must not see fake Avoid verdicts).
Then open `/#judge` on the projector — QR code now points at your real domain.

## 2-minute pitch (details in docs/devpost.md, Q&A in docs/judge-qa.md)
0. Open `BASE/?demo=1` in a fresh tab (check: `/?demo=1#drive` shows sample route chips + Simulate storm).
1. **Home** → "Set my place" (or "Try a sample address") → `5300 N Braeswood Blvd, Houston, TX 77096` → summary: "Flooded in Harvey (2017)", Zone AE, ZIP 77096: 6,482 NFIP claims. Expand "Flood history here" (Harvey: major) and "Renting or buying here?" (median premium ~$1,501).
2. **Drive Safe** (`BASE/?demo=1#drive`) → click demo route chip "Downtown: Allen Parkway underpass" → turn on the **Simulate storm** toggle on the Drive page → Check route → **Avoid** with named crossings. The same switch (on Home, Alerts and Drive; one setting per tab) also turns Home into the storm view: "Simulated" tag, an alert labelled "SIMULATED — demo only", and caution routes say "Simulated storm: conditions are active". Turn it off before showing real data.
3. **Replay** → Hurricane Harvey → Play + **Narrate**.
4. **Seabrook evacuation** → search `Seabrook, TX 77586` (test point 29.564, -95.025; warmed by `scripts/prewarm.py`) → summary shows **Evacuation Zone A** + "Up to 9+ ft storm surge (Cat 3+)" chip, a Galveston tide card, and (in "Your place's flood profile") "No Harvey extent data" (Harvey layer covers only the City of Houston, so no false all-clear). Expect no out-of-region storm chip.
5. **Voice mode** → Ask → switch **Type / Talk** to Talk → tap the mic, then hold to talk (or hold space) → say "Did my neighborhood flood before?" → spoken answer in about 1 s (measured 0.64-1.4 s) → interrupt mid-answer (barge-in) → follow-up in Spanish. If it stalls: Retry / "Switch to typing". Typed Ask median is 228 ms.
6. **Ask** (Spanish): switch language to Español (EN menu, top right) → "¿Qué hago si mi calle se inunda?" → sourced safety steps, 911.
7. **Alerts** (`#alerts`) → turn on "Alerts on this phone" (allow notifications first) → "Simulate storm alert" → phone buzzes. Disabled until notifications are allowed. Optional: Judge-page SMS simulator (demo mode) → `ALERTS ON`.
Note: the in-app Judge page lists 5 guided steps (Risk, Avoid, Replay, Spanish, Push); Seabrook and Voice are only in this script.
Optional extras (30 s each): Ask → open "How I answered" under an answer (intent, sources, tools, model/template) · Recover → FEMA declaration banner, proof-of-loss, appeal, scam and floodwater cards · Prepare → dialysis centers with FEMA zone / Harvey badges · go offline → `#offline` safety card · Judge page → "Evidence (checked, dated)".
Close: "Reduces harm for **33 of 52** documented Houston flood problems, 5 fully and 28 partly (problem-by-problem audit with live tests: `docs/problems/`); the other 19 are mostly policy problems we make visible and actionable."

## What's measured (say it, Judge page shows it dated)
240 backend tests · AI eval 38/40 · citation eval 15/15 (live Gemini) · voice median 1.4 s end of speech to first audio (n=3, small sample) · axe 0 violations in 48 combos · demo_check 21/21 online and in snapshot mode (138 snapshots incl. /declarations) · coverage 33/52 (5 fully, 28 partly). Not official guidance; in danger call 911.

## Voice mode needs a real mic check
The live-mic loop is verified with a fake mic only (CHANGELOG, "Live talking verified"). Do one real-mic run on the demo laptop and browser before judging.

## Say before they ask (limitations)
Shelter list is 2017 Harvey data (labeled historical) · 128 crossings (KPRC list, USGS high-water marks, OSM underpasses; not a complete inventory) · Harvey extent is City of Houston only (357,241 polygons; elsewhere "no Harvey extent data") · vi/zh/ar translations are AI-reviewed, pending native-speaker review · SMS is simulated unless Twilio keys are set · elevation fallback approximate · AI answers without a key are templated from sourced cards.

## Before judging: run the backend WITHOUT auto-reload
Hot-reload drops live voice sessions. Stop the dev backend and run:
`cd backend && uv run uvicorn app.main:app --port 8000` (no --reload). Production (Docker) already runs without reload.

## Gemini quota (free tier)
Quotas are per model and per project. Don't run `eval_ai.py` (live) before judging. Optional backup: create a 2nd key in a NEW project at aistudio.google.com/apikey and add `GEMINI_API_KEYS=<key2>` to `.env`, then restart the backend. `/#status` shows the active Gemini model.

## Wi-Fi fails (offline snapshot mode)
Recorded responses for every demo step live in `data/demo_snapshot/` (re-record while online: start a no-key backend on :8070 with `GEMINI_API_KEY= ELEVENLABS_API_KEY= uv run uvicorn app.main:app --port 8070`, then `cd backend && uv run python ../scripts/record_demo.py`, then stop :8070).
If the venue network dies, restart the backend with:
`cd backend && DEMO_SNAPSHOT=1 uv run uvicorn app.main:app --port 8000`
Every recorded request is answered from the snapshot (header `X-FloodReady-Snapshot: 1`, meta.freshness "snapshot") and the app shows an "Offline demo data from <time>" banner. Ask uses 6 canned answers (pitch questions, templated from the knowledge cards); voice shows "Voice needs internet" and falls back to browser speech. Without `DEMO_SNAPSHOT=1` snapshots are never used (the snapshot layer is not installed), so restart with the flag as soon as the network looks shaky. Demo mode also lets the SMS simulator save ALERTS ON/OFF and STOP/START (same as `SMS_SIMULATE=1`). Tip: put the laptop and phone on your phone hotspot (the app only needs localhost + the phone for push); for the phone, open `http://<laptop-LAN-IP>:5173`.

## If something breaks
- Backend down: `cd backend && uv run uvicorn app.main:app --port 8000`
- Frontend down: `cd frontend && npm run dev`
- Any tab errors → other tabs still work (error boundaries); in danger copy always shows 911.

## Refresh evidence numbers
`python3 scripts/build_evidence.py` (runs backend pytest; rewrites frontend/public/evidence.json from docs/eval/*, cycle-35 coverage; fails if a source is missing).
