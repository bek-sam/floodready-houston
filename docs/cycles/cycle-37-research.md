# Cycle 37 research: offline resilience (phone loses data/power in a storm)

Tested on the production build (`npm run build`, `vite preview :4173`, which proxies /api to :8000), Playwright mobile 390x844, `context.set_offline(True)`. The preview server was stopped afterwards.

## What already works offline (after pages were opened once online)
- App shell loads from the SW cache. The "In danger? Call 911" strip shows on every page (src/App.tsx).
- `OfflineBanner` ("You're offline. Your saved place, plan and safety steps still work.") shows in the shell on all routes (src/components/shell/OfflineBanner.tsx).
- Home: shows the last risk summary from localStorage (`useSrc` cache in src/pages/Home.tsx) with a "Offline: showing results from 7:33 AM" chip. Updated time and live conditions render.
- Prepare tabs, go-bag (saved checkbox progress), 211/311/911 `tel:` buttons (EvacuationHelp), Civic officials (SWR-cached /api/civic), Replay, Recover (checklist, 911 button), Settings (once visited) all render.

## Gaps, ranked

1. **Cold offline reload can blank the whole app (P0).** A fresh SW install precaches `/assets/*` via `cache.add()`. A later offline module-script request has an `Origin` header. If the server sends `Vary: Origin` (vite preview does), `cache.match(req)` misses, `networkFirst` falls back to `caches.match('/')`, and the JS request gets text/html. Result: no `<main>`, blank page, "Failed to load module script ... text/html". Repro: load Home online, wait 4 s, go offline, reload. Lazy chunks never visited online (Settings) show "This section had a problem". Caddy (deploy/Caddyfile) probably does not send Vary: Origin, so the risk in production is unverified.
   Fix in `frontend/public/sw.js`: use `cache.match(req, {ignoreVary:true})` and `caches.match(req, {ignoreVary:true})`. For non-navigate requests never fall back to `/` HTML. Return `Response.error()` (a 503 with no body) instead.
2. **No plan offline unless built online beforehand (P1).** `lastPlan` is saved only after the user taps "Build my plan", which calls /api/plan. On a fresh device the steps are empty offline and "Build my plan" shows the generic "cannot reach server" error. Ready.gov says to prepare the family plan and a paper copy in advance. Fix in `src/pages/Prepare.tsx` (`runPlan`): on an ApiError with status 0, build a deterministic client-side plan from the household (static "now/storm/after" steps with sources). Also auto-save a plan after the first online Home load.
3. **Ask, Alerts and Drive have no offline path (P1).** Ask returns "I couldn't answer that right now" (no local knowledge fallback). Alerts shows "We couldn't check this place right now" plus the server-unreachable error and no last-known status. Drive shows only an error. Fix:
   - Alerts (`src/pages/Watch.tsx`): cache the last `/watch/status` per place in localStorage, and show it with "as of <time>".
   - Drive: surface the existing `floodready.lastRoute`, and note that "Never drive through flooded roads" still applies.
   - Ask: pre-cache top FAQ answers, or send the user to the offline safety card (item 4).
   - Add `/api/watch/status` to SW CACHEABLE_API only if the staleness label is shown.
4. **No single "offline safety card" (P1).** Offline 911/311/211, the family meeting place and out-of-area contact, the go-bag, and the 3 key rules (turn around don't drown, move to high ground, no generators indoors) are scattered over four pages. Fix: add a `#offline` card in the shell, linked from `OfflineBanner`, built from localStorage only (family plan `FAMILY_KEY`, household, go-bag). Add a Print / "Save as image" action for the wallet card. Ready.gov lists paper copies, written contacts and a printed Family Communication Plan.
5. **Freshness labels are inconsistent (P2).** Only Home shows "showing results from <time>". The SW SWR endpoints (civic, shelters, outlook, replay) serve stale JSON silently. Fix: the `api.ts` `req()` wrapper reads a `Date`/`X-FloodReady-Cached` header, or sets a timestamp in the SW response, and the Civic/Shelters cards show the age. The banner could say "last updated <time>" using the Home cache `at`.
6. **Power loss (P2).** Add a "save battery" tip near the banner or go-bag: low-power mode, dim screen, text rather than call (FEMA/Ready.gov: power bank and backup battery). Ready.gov's power-outage page does not cover texting vs calling, so keep that tip sourced from FEMA or the Red Cross if added.
7. **Offline-aware prefetch (P3).** After onboarding or place save, warm `/api/civic`, `/api/shelters`, and the harvey/crossings meta so the first offline visit has data. Today the SWR cache fills only on a prior visit.
8. **Map tiles (P3).** OSM tiles are cross-origin and go straight to the network, so Drive and Replay maps are blank offline. Ready.gov: "Carry local maps in case you can't use your phone." Print a map or screenshot from the offline card.

## Authoritative guidance used (prioritization)
- FEMA/Ready.gov Emergency Kit: https://www.ready.gov/kit. Phone chargers plus a backup battery, battery or hand-crank radio and NOAA Weather Radio, local paper maps, paper or waterproof copies of insurance, ID and bank records, and paper and pencil for notes.
- Ready.gov Make a Plan / Communicate: https://www.ready.gov/communicate. Know how to contact each other and reconnect if separated, a written family plan with contacts, meeting place and medical info, a printable Family Communication Plan card, and a plan for receiving alerts.
- Ready.gov Power Outages: https://www.ready.gov/power-outages. Backup power (power bank), unplug electronics against surges, keep generators dry (shock risk in floodwater).

Priority from this guidance: (1) contacts and meeting place, (2) emergency numbers, (3) documents, (4) maps, (5) battery. This matches fixes 1, 4, 2 and 6 above.
