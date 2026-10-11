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
4. **Ask** (Spanish) → "¿Qué hago si mi calle se inunda?" → sourced safety steps, 911.
5. **Watch** → Simulate storm push → phone buzzes.
Close: "Directly reduces **33 of 52** documented Houston flood problems; the other 19 are policy problems we make visible and actionable."

## Say before they ask (limitations)
Shelter list is 2017 Harvey data (labeled historical) · crossings from one KPRC list (64) · Harvey extent covers 4 demo areas, simplified · elevation fallback approximate · AI answers without a key are templated from sourced cards.

## Before judging: run the backend WITHOUT auto-reload
Hot-reload drops live voice sessions. Stop the dev backend and run:
`cd backend && uv run uvicorn app.main:app --port 8000` (no --reload). Production (Docker) already runs without reload.

## Gemini quota (free tier)
Quotas are per model and per project. Don't run `eval_ai.py` (live) before judging. Optional backup: create a 2nd key in a NEW project at aistudio.google.com/apikey and add `GEMINI_API_KEYS=<key2>` to `.env`, then restart the backend. `/#status` shows the active Gemini model.

## If something breaks
- Backend down: `cd backend && uv run uvicorn app.main:app --port 8000`
- Frontend down: `cd frontend && npm run dev`
- Any tab errors → other tabs still work (error boundaries); in danger copy always shows 911.
