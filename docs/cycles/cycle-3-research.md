# Cycle 3 Research (Sat Oct 10 2026, ~7 PM)

Method: curl against :8000/api walking docs/devpost.md pitch script, plus code reads. No browser. Health: all keys false (gemini, elevenlabs, backboard, db).

## 1. Demo walk (backend)

| Step | Endpoint | Result |
|---|---|---|
| Know risk, Meyerland | geocode 1.1s (fallback Nominatim for street addrs), risk 1.06s | OK. FEMA AE, sfha true, but `low_ground: null` ("no gauge datum") and no Harvey field seen in first 350 chars (verify `harvey` in UI). Geocode "5100 Chimney Rock" lands at an Elks Club (wrong); use "Meyerland Houston" (instant, 29.6786,-95.464) or "5555 Beechnut St" (0.3s, Census). |
| Drive Safe | route-check/demo; POST route-check Allen Pkwy | Works. Without storm "caution" (2 crossings), with `?simulate=storm` "avoid". ~1.0s. Good. |
| Replay | /replay/events ok; /replay/harvey-2017 0.05s | Works (ids use hyphen). 26 gauges, but several have null flood stages (San Jacinto at Lake Houston all null; Cedar Bayou/Clear Creek above Telephone moderate/major null) so those render stage-less. |
| Watch + push | /push/simulate returns `{"sent":0}`; watch/status with unknown id returns empty | Expected without a subscription, but means demo fails unless phone is subscribed (checklist item 1). No fallback visible on laptop. |
| **Ask in Spanish** | POST /ask "Que hago si mi calle se inunda?" and the accented form | **FAILS**: "No tengo informacion con fuente sobre eso", sources [], generated_by template. This is the exact pitch line (1:45). |
| Ask English equivalent | "What should I do if my street floods?" | Weak: returns buyout/renters text with unrelated sources, nothing about driving/evacuation. "Is it safe to drive through flooded road" returns one line only. "No car" question is good now (STEAR/211). |
| Voice | POST /voice | 503 without ElevenLabs key; frontend falls back to speechSynthesis (es voice usually exists on Mac/iOS). |
| Outlook / shelters | /outlook, /shelters need lat&lon (422 without) | Fine if frontend always passes them. Outlook says "No excessive rainfall" today: calm, not a bug. |
| Alerts | /alerts | Returns Ozone Action Day (severity Unknown, long raw text) at the top of Home/Watch; must be confirmed collapsed in UI. |

Slow (>3s): none. Slowest is 1.1s.

## 2. Sponsor gaps (smallest credible integration)

- **Gemini**: no key set, so every demo answer is "template". Smallest: set GEMINI_API_KEY on the demo box, verify `generated_by:"gemini"` for /ask and /plan, and show a "Powered by Gemini" chip from `generated_by`. Also fix template fallback so the key-less run is not embarrassing.
- **ElevenLabs**: key-less = 503. Smallest: set key, pre-generate mp3s for the 5 language "storm warning" phrases and the Replay narration into `frontend/public/audio/`, serve statically, and have `speak()` try the static file first. Works even if key or network dies.
- **Tiger Data**: only `reports` becomes a hypertable (db.py:79), and only when DATABASE_URL is Postgres+timescaledb. Nothing time-series is user-visible. Smallest: add a `gauge_readings(gauge_id, observed_at, stage_ft)` hypertable, write a row whenever /risk or /watch/status fetches gauges, and add `/api/gauges/{id}/trend` using `time_bucket('1 hour', ...)`; show a small sparkline in Risk. Needs a free Tiger Cloud service + DATABASE_URL.
- **Backboard**: best effort, writes profile as a message only (memory.py). Smallest: at /ask, when a profile id is supplied, fetch/append to the Backboard thread and show "Remembered from your profile: renter, no car" in the answer; show a Backboard badge on /profile when `backboard_assistant_id` is set. Needs key.
- **Vultr**: deploy script exists, but no live URL confirmed. Smallest: deploy now, put the live URL in README and Devpost, screenshot `curl /api/health`.
- **GoDaddy Registry**: Caddy takes DOMAIN; no domain claimed. Smallest: claim a .tech/.xyz free-with-MLH domain, point A record at Vultr, set DOMAIN, put it in Devpost and on the QR page.
- **DEV**: needs a published post tagged `#mlhacks`; convert devpost.md into it (15 min).

## 3. CHANGELOG leftovers

- Non-English cue keywords (carro, diálisis, calle, inunda, evacuar): confirmed cause of the Spanish miss above. Cheapest fix: translate Spanish question to cue words via a small es/vi/zh/ar keyword map before intent/BM25, or add Spanish aliases to chunk headings.
- "Install app" untranslated, `home.noRiskToday` not wired (still reads as reassurance).
- Intent for "street floods" should map to the evacuation/drive/what-to-do chunks, not buyout.

## 4. Immersive upgrades (<=2h)

- Animated Harvey replay: auto-play button plus a rising water-level bar/overlay colored by flood stage as the slider moves (1h). Data already complete.
- Replay narration: 5 pre-generated captions ("Aug 26: Brays Bayou hits action stage...") spoken at the matching timestamps via static mp3 or speechSynthesis (45 min).
- Judge QR page `/judge`: QR to the live domain, 4-button "try this" script (Meyerland, Allen route storm, Replay Harvey, Ask in Spanish) and a keys status line (30 min).
- Storm-simulation on-screen banner that sets all pages into storm mode so Home, Drive and Watch change together (30 min).

## Top 6

1. Fix Ask for the pitch line (es and en "my street floods") with cue keywords and a canned evacuation answer; verify before demo. Highest risk, lives in the script.
2. Set Gemini and ElevenLabs keys on the demo box and pre-generate static audio; two prizes and the fallback chip.
3. Deploy to Vultr with a GoDaddy-registry domain; put live URL in Devpost (three prizes, Completion).
4. Tiger Data: `gauge_readings` hypertable plus trend sparkline on a Tiger Cloud DATABASE_URL.
5. Animated Replay with water level and spoken narration (Immersive and Best Pitch visual).
6. Judge `/judge` QR page plus DEV `#mlhacks` post and Backboard "remembered profile" badge.
