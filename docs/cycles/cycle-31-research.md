# Cycle 31 research: accessibility + performance audit (running app, no code edited)

Method: axe-core 4.10.2 on 12 views (11 routes + fresh-storage onboarding) x 390x844 / 1280x900 x light/dark (theme key `localStorage.theme`), place seeded to 5300 N Braeswood. Playwright keyboard walk. Production build timings via `frontend/dist` served statically (API forwarded to :8000). Raw data: scratchpad `e2e/c31/axe.json`.

## Ranked findings

### A11y
1. **Serious, color-contrast, About, dark theme (both viewports)**. `.text-white` on `bg-brand` is 2.21:1 (white on #6cb4f5). Source: `frontend/src/pages/About.tsx:31` (demo button, `bg-brand ... text-white`). In dark mode `--brand` is light, so use `text-bg dark:` / an `on-brand` token (as EmergencyStrip does with `text-white dark:text-bg`). Same pattern anywhere `bg-brand ... text-white` is used is suspect, but axe only flagged this one.
2. **Moderate, region, all 12 views (48 hits)**. Content outside landmarks: the emergency strip (`components/shell/EmergencyStrip.tsx`, the "Call 911" link text and its `.opacity-80` sub-text) and, in onboarding, the `.text-[17px]` text. Fix: wrap `<EmergencyStrip>` in `<aside aria-label="Emergency">` (or `role="region"`), and put Welcome content in `<main>`. Low risk, removes every remaining region hit.
3. **Moderate, heading-order, 390px only: prepare, ask, replay, recover, civic, settings, about**. An `<h3>` follows the `h1` with no `h2`. It sits in the first `<section>`'s header (`.mb-3.justify-between > div > h3`, the shared section-header component in `components/ds`). Fix: let the component take a `level` prop or render `h2`. It only appears on mobile, probably because the desktop layout renders the h2 PageHeader.
4. No critical violations. Zero violations on Home, Alerts, Drive, Ask, Compare in any theme or viewport for color-contrast, labels, names, target size.

### Keyboard (Home, Drive, 390 + 1280)
- Every stop has a visible focus ring (3px solid outline, 0 stops without). No traps. Drive tab loop is 26 stops (mobile) / 32 (desktop) and cycles cleanly.
- Native `<dialog>` Sheet (`components/ds/Sheet.tsx`): My place and Language sheets receive focus inside on open, Esc closes, and focus returns to the trigger button. Good.
- Skip link works, but on route load focus is moved to `<main>`, so DOM order is main content, then bottom nav, then skip link/911/header (these come AFTER main on Tab; a keyboard user pressing Tab right after load never meets them unless they wrap or use Shift+Tab). Minor: render the skip link and 911 strip first in DOM (they already are, per source), and only call `main.focus()` on route change, not on first load, or set sequential focus start to the document top.
- Home has 38 tab stops; 6 "Explain:" chip buttons and 3 "What this level means" buttons precede the primary actions. Acceptable, optional polish.

### Performance (production build)
Largest chunks (raw / gzip):
| chunk | raw | gzip | loaded on Home? |
|---|---|---|---|
| Replay3D | 1,051 KB | 281 KB | no (lazy, Replay only) |
| index (main) | 775 KB | 250 KB | yes |
| ElAgentTalk | 580 KB | 151 KB | no (lazy, Ask engine C) |
| maplibre-gl-worker | 508 KB | n/a | no |
| leaflet | 165 KB | 48 KB | yes (Home) |
| Home | 54 KB | 16 KB | yes |
Initial Home JS is about 773-927 KB raw (~300-330 KB gzip). The 775 KB main chunk is the only real cost; it triggers Vite's >500 KB warning. Inspect what is in `index` (probably the i18n string tables for 6+ languages plus lucide icons; split translations per language or lazy-load non-en dictionaries to cut it). Fonts: Inter woff2 subsets 85 KB + 48 KB + 26 KB (browser only fetches subsets it needs).

Home load (390x844, local, headless, API warm in cache):
- Production build: first `h1` 0.85 s warm / 1.59 s cold, FCP 68-88 ms, LCP 0.44 s warm / 1.63 s cold, network idle 0.9-2.1 s.
- Dev server: h1 0.55 s, LCP 0.55 s (many more requests, 6.2 MB unminified JS).
- Cold-run 1.6 s is the lazy chunk plus first API wave; no API is the cause (see next).

Home API timings (all calls, fastest to slowest, warm): risk 32-52 ms, coastal 35-42, rain24 26-36, alerts 9-34, evac 8-34, hwm 12-34, flood-history 10-34, outlook 1-35, gauge histories 3-8 ms. **No API on Home exceeded 1.5 s** (max 52 ms; these are cached/snapshot responses, so a cold upstream could differ). Home fires 11 API calls on load; fine on HTTP/2 but consider a single bundled `/home?lat&lon` endpoint if mobile latency matters.

## Suggested fixes in priority order
1. About.tsx:31 contrast in dark mode (1-line).
2. Wrap EmergencyStrip in a labelled landmark; wrap Welcome in `<main>` (clears all `region` hits).
3. Section header heading level (clears 7 mobile heading-order hits).
4. Split the 775 KB main chunk (dictionaries per language).
5. Don't steal focus to `<main>` on first load (skip link reachable).
