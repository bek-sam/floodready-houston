# Cycle 4 research/QA (code-level, no browser)

## 1. Demo-breakers
- backend/app/ai/router.py:33 /ask has no rate limit and `question: str` has no max_length (also /voice text, :26) -> add Field(max_length=500) + simple per-IP limiter (e.g. 20/min).
- backend/app/routers/push.py:62 /push/simulate is unauthenticated and pushes to ALL subscribers; any visitor (QR on /#judge) can fire it -> require header token from .env or disable unless DEMO=1.
- push.py:58 /push/test same; and :52 /push/unsubscribe `endpoint=None` filter is harmless but unvalidated -> 422 if empty.
- frontend/public/sw.js:5 SWR on /api/risk, /api/crossings, /api/shelters: first view after a change shows stale data (seen only on next load); live demo of changing risk looks "stuck" -> drop /api/risk and /api/crossings from CACHEABLE_API, or use network-first with 3s timeout.
- sw.js:15 precaches only '/', navigations cached as '/' (SPA); a stale index.html after redeploy references missing hashed assets -> bump SHELL version on each deploy (v3) before Sunday.
- sw.js:21 swr(): when no cache and fetch fails, `.catch(() => hit)` resolves undefined -> respondWith(undefined) throws; return `Response.error()` fallback.
- frontend/src/pages/Watch.tsx:35-44 poll() has no in-flight guard; toggling `sim` or adding a place restarts the interval and overlapping responses can arrive out of order and overwrite newer `status` -> use a request counter/AbortController.
- Watch.tsx:41 prev level map isn't reset when `sim` toggles, so turning sim off then on never re-fires the alert; turning sim on first poll sets prev only -> reset prev.current in the sim onChange (the demo moment: first sim poll won't alert if prior level already watch).
- Watch.tsx:49 poll() has no `try` around `places.map` result when API returns non-array `places` -> guard `r.places ?? []`.
- Ask.tsx:6-7 `window.SpeechRecognition` read at module load; fine, but mic():`r.start()` can throw InvalidStateError on double-tap (unhandled) -> wrap in try/catch.
- Ask.tsx:35 on error path ErrorBox lacks retry; the failed question is lost -> keep `q` on error.
- main.py:25-33 CORS allows only localhost:5173; after Vultr deploy with a separate origin, all API calls fail -> add the deployed domain (or keep same-origin proxy and say so).
- Judge.tsx:11 QR encodes location.origin: shows localhost until deployed (known) -> open /#judge from the public URL only; add a VITE_PUBLIC_URL override.
- StageChart.tsx:11 R=118 right gutter in a 640 viewBox: at 375px the svg scales ~0.55 so 11px labels render ~6px (illegible) -> use fontSize 18 in viewBox units, or shorten labels ("Mod 12").
- StageChart.tsx:50 label de-bunching only pushes downward; with 4 close thresholds the last label may exceed H-B and clip under the x-axis -> clamp lyRef to <= H-B-2.
- StageChart.tsx:39 `yMin=Math.min(0,...)`: scale from 0 compresses thresholds (cycle-3 leftover) -> yMin = max(0, minData - 10% range).
- WaterTube.tsx:33-35 label x=X+TW+14=78 with text "Moderate 25 ft" fits in 260, but labels at close y collide (no de-bunching like StageChart) -> reuse the 13px spacing pass; also clipPath id="tubeclip" is not unique (two tubes on a page share id) -> useId().
- Replay.tsx:42 interval 80 ms + setIdx in updater calling setPlaying (side effect in updater, double-run in StrictMode) -> move end check to an effect.
- Replay.tsx:62 speak() on each crossing with no cancel of the previous utterance -> call stopSpeaking() first.

## 2. Fact consistency vs research-brief.md
- risk.py:60 "154,170 ... only 36% insured" matches brief:31 (source SRC_HARVEY OK).
- risk.py:57 and i18n.ts:28 "nearly half ... outside 100/500-year" matches brief:73; brief:31 says "~half" - fine.
- graph.py:124 pulls "77%" from driving-in-floods.md; brief:51 qualifies it as "77% of TEXAS flood deaths (1959-2008)". Ensure UI copy includes "Texas" and the period; grep found no "1959" in frontend/backend -> add "(Texas, 1959-2008)".
- "6th": no occurrence in frontend/backend/knowledge (brief:11 "#6" is ozone, not flood) -> nothing to fix; do NOT show it in flood copy.
- "30 days": graph.py:311 and insurance.py:12 say "generally 30 days" - OK; confirm every mention keeps "generally" (exceptions: loan closing, map revision).
- "92%": only in data/knowledge/insurance-30-day-and-gap.md:10, labeled as spoken quote - OK; no UI usage found. Keep it that way.
- risk.py:60 fact has no `source` for the 36%: confirm SRC_HARVEY is the communityimpact URL (brief:31), not the khou NHC one.

## 3. Accessibility
- Watch.tsx:98 status chip pairs icon + text (good). Drive/Home status chips: verify StatusChip (ui.tsx) always prints text, not color only.
- Watch.tsx:95 `<input type=checkbox>` inside label OK; but Judge.tsx:23 checkbox list has no aria group; low priority.
- Ask.tsx:99 mic button uses `aria-label` but icon-only 🎤/● alone for pressed state; OK. Send/Remove buttons are text - fine.
- App.tsx:114 7-tab bottom nav at `text-[10px]` on 375px (53px/tab) - tap targets min-h-14 OK, text below 12px and likely truncated in vi/zh/ar -> text-[11px] + truncate + aria-label.
- StageChart.tsx:75 svg role="img" hides the hover tooltip from keyboard/SR users; table toggle covers it (good). Chart "Chart/Table" button text is hard-coded English (:55) -> use t().
- Hard-coded English in Watch.tsx:56 "Flood WARNING"/"Flood watch" notification titles and :111 "(demo)" -> t().
- Judge.tsx:17 QR has aria-label with URL (good).
- Ask.tsx:60 `aria-live="polite"` wraps whole message list: SR re-reads all on update? (only appended nodes announce; fine).

## 4. Security basics
- No API keys/secrets in frontend/src or vite config (grep clean); .env loaded server-side only. OK.
- CORS: allow_methods/headers "*" with an origin allow-list - fine; see deploy note above.
- Input limits missing: AskBody.question, VoiceBody.text, PlanBody.profile (ai/router.py:14-26); geocode address param (routers/geocode.py) -> max_length 300/500, profile size cap.
- /reports GET `limit` can be negative (reports.py:41 `min(limit,1000)`) -> ge=1 via Query.
- /watch POST (watch.py:26) creates unbounded Place rows per call; /reports POST unauthenticated -> per-IP limit (slowapi or a 30-line in-memory limiter middleware).
- Md renderer (Ask.tsx:14) builds links from model output via React nodes, not innerHTML (safe); Judge.tsx:18 dangerouslySetInnerHTML uses QR lib output only (safe).
- Md `href` accepts any `https?:` URL from the model - OK, rel=noreferrer set.

## Top 8 by demo risk
1. /push/simulate + /push/test open to anyone with the QR (push.py:58-64): a judge's phone could spam everyone -> token/DEMO flag.
2. sw.js stale shell/API after Sunday redeploy (sw.js:2, :5): bump cache version, drop /api/risk and /api/crossings from SWR.
3. sw.js:21 swr() returns undefined offline with empty cache -> Response.error() fallback.
4. CORS + QR origin (main.py:27, Judge.tsx:11) break on the Vultr domain -> add domain, test from phone.
5. Watch.tsx poll race + prev not reset on sim toggle (Watch.tsx:35-44): the headline simulated-alert demo may not fire.
6. /ask unlimited and no length cap (ai/router.py:20,33): cost/abuse and slow answers under judge load.
7. StageChart/WaterTube label size and collision at 375px (StageChart.tsx:11,50; WaterTube.tsx:33).
8. 77% copy missing "Texas, 1959-2008" qualifier (graph.py:124): judges may fact-check.
