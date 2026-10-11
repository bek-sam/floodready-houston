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
4. **Phone push test**: open the deployed URL on your phone → (iPhone: Share → Add to Home Screen → open from Home Screen) → Watch → add a place → Enable push alerts → Simulate storm push.

## 30 minutes before judging
```
cd backend
uv run python ../scripts/prewarm.py  BASE   # warm caches (BASE = https://yourdomain or http://localhost:8000)
uv run python ../scripts/demo_check.py BASE --front   # must say 21/21 passed
```
Open `/#judge` on the projector — QR code now points at your real domain.

## 2-minute pitch (details in docs/devpost.md, Q&A in docs/judge-qa.md)
1. **My Risk** → `5300 N Braeswood Blvd, Houston, TX 77096` → "Flooded in Harvey (2017)", Zone AE, flood history (Harvey: major), ZIP 77096: 6,482 NFIP claims, median premium ~$1,501.
2. **Drive Safe** → demo route "Allen Parkway underpass" + Simulate storm → **Avoid** with named crossings.
3. **Replay** → Hurricane Harvey → Play + **Narrate**.
4. **Seabrook evacuation** → search `Seabrook, TX 77586` (test point 29.564, -95.025 in `backend/tests/test_evac.py`; it is NOT in `prewarm.py`, so run it once before judging) → summary shows **Evacuation Zone A** + storm-surge depth chips, the Galveston tide chip, and "No Harvey extent data" (Harvey layer covers only the City of Houston, so no false all-clear). Expect no out-of-region storm chip.
5. **Voice mode** → Ask → **Voice** (Gemini Live, default) → say "Did my neighborhood flood before?" → spoken answer in about 1 s (measured 0.64-1.4 s) → interrupt mid-answer (barge-in) → follow-up in Spanish. If it stalls: Retry / "Switch to Standard". Typed Ask median is 228 ms.
6. **Ask** (Spanish) → "¿Qué hago si mi calle se inunda?" → sourced safety steps, 911.
7. **Watch** → Simulate storm push → phone buzzes. Optional: Judge-page SMS simulator (demo mode) → `ALERTS ON`.
Close: "Directly reduces **33 of 52** documented Houston flood problems (strict recount: `docs/cycles/cycle-24-coverage.md`); the other 19 are mostly policy problems we make visible and actionable."

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
Every recorded request is answered from the snapshot (header `X-FloodReady-Snapshot: 1`, meta.freshness "snapshot") and the app shows an "Offline demo data from <time>" banner. Ask uses 6 canned answers (pitch questions, templated from the knowledge cards); voice shows "Voice needs internet" and falls back to browser speech. Without `DEMO_SNAPSHOT=1` the same snapshots are used automatically if a request errors. Tip: put the laptop and phone on your phone hotspot (the app only needs localhost + the phone for push); for the phone, open `http://<laptop-LAN-IP>:5173`.

## If something breaks
- Backend down: `cd backend && uv run uvicorn app.main:app --port 8000`
- Frontend down: `cd frontend && npm run dev`
- Any tab errors → other tabs still work (error boundaries); in danger copy always shows 911.
