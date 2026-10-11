# Cycle 25 research (Sun Oct 11, ~3:50 AM, freeze 11 AM)

Constraints: each idea is at most 1.5 h, uses free data, needs no runtime Gemini. Not yet built (grep of `frontend/src` and `backend/app` finds no iframe/embed and no `gridpoints`/`quantitativePrecipitation`). Curl tests were run Oct 11 with a plain User-Agent.

## Verified or refuted

| Direction | Curl result | Verdict |
|---|---|---|
| NWS gridpoint (HGX/63,95 for downtown) | `/points/29.76,-95.37` 200. `/gridpoints/HGX/63,95` returns `quantitativePrecipitation` in mm, 33 values in **6-hour** steps (not hourly), plus `updateTime`. `/forecast/hourly` returns 156 hourly periods with `probabilityOfPrecipitation` (%) and `shortForecast` | Works. Chart = 6 h QPF bars + hourly PoP line. Do not call it hourly rainfall |
| METRO alerts | `ridemetro.org/alerts` 200 HTML ("Service Alerts and Detours"). Guessed GTFS-RT URLs 404 | No public feed found. Link-out only |
| TxDOT / DriveTexas | `drivetexas.org` 200. Guessed API endpoints 500/404, ArcGIS URL invalid | No verified API. Link-out only |
| HISD closures | `houstonisd.org` 200. `/emergencyalerts`, `/news` 404 | Link to the homepage only, no feed |
| CenterPoint outages | `centerpointenergy.com/outage` 200. Other guessed paths 404 | Link-out to `/outage` only |
| FloodSmart | `floodsmart.gov` 200, `/flood-insurance-cost` 200 ("Get Insured"). `/find-an-agent`, `/get-flood-insurance-quote` 404 | Source the checklist to these two pages only |
| Power / heat | `ready.gov/power-outages` 200, `weather.gov/safety/heat` 200, `weather.gov/safety/flood-after` 200. CDC heat page 403 to curl (unverified) | Cite Ready.gov and NWS only |

## Ranking

1. **Park-my-car check** (A9 INFORMS to REDUCES). The only idea that moves a problem. About 1 h.
2. **Rain next 24 h at my place** (NWS QPF + hourly PoP). About 1.25 h.
3. **Embeddable partner widget** (iframe snippet). The best partner/reach story. About 1.25 h.
4. **Family plan share link**, URL-encoded with no server. About 1 h.
5. **Closures and outages link hub** (METRO, DriveTexas, CenterPoint, HISD). About 0.75 h. This stays INFORMS, because link-outs do not change what a user can do at an address.
6. **Insurance quote checklist + power-outage heat card**. About 1 h. Text only, so INFORMS.

Honest note: only #1 truly flips a row. The others deepen counted rows or are "wow" features. Do not claim more than 34 of 52 even after #1. Update the pitch only if #1 passes the cycle 24 test.

## Top 4 specs

### 1. Park-my-car check (owner: `frontend/src/components/parking/`, backend reuse)
- Action: the user saves "where I park" (an address, or the My place address) and gets a verdict from existing `/api/risk`. If FEMA zone is AE/VE, Harvey flooded is true, or the point is near a known underpass (`data/crossings.geojson`), the card says "Move your car to higher ground before heavy rain".
- Hooks: when Watch level is watch/warning or the rain outlook badge is elevated, show a banner on Home with "Move car" and a Maps link. Add a one-tap `.ics` "move car" reminder, reusing the season .ics code.
- Data: the parked location stays on device (localStorage), like buddy check-in. No new network source.
- Honest limits: "flood-prone based on records, not a prediction for this storm". Source chips copy the risk card. Never say "safe".
- i18n: add keys for 5 languages; run `scripts/i18n_coverage.mjs`.
- Tests: one backend-free vitest for verdict logic. Finish with a build and a browser shot.
- Coverage: A9 moves from INFORMS to REDUCES. Re-run the cycle 24 test before claiming.

### 2. Rain next 24 h at my place (owner: `backend/app/routers/rain24.py`, `frontend/src/components/rain24/`)
- Endpoint: `/api/rain24?lat&lon` calls `api.weather.gov/points/{lat},{lon}`, then `gridpoints/{wfo}/{x},{y}` for `quantitativePrecipitation` (convert mm to inches, 25.4 mm/in, keep the 6 h windows that overlap the next 24 h) and `/forecast/hourly` for hourly PoP. Return `meta{as_of: updateTime, source, freshness}` like the other data endpoints. Cache 15 min. NWS requires a User-Agent. On failure return unavailable and show "rain forecast unavailable"; never show zero rain.
- UI: Home details card with four 6 h bars (inches) and an hourly PoP sparkline. Labels say "Forecast amounts are NWS model estimates, 6-hour totals". It links to `weather.gov`. It sits next to the WPC outlook badge.
- Action line (rule-based): if any 6 h window is at least 1 in or hourly PoP is at least 60%, show "Leave before [window start] if you need to cross a flood-prone road" with a Drive link. Do not give a "safe" claim.
- Tests: mocked NWS JSON for parse and unit conversion, plus the failure case. Add the source to `/api/status` and the prewarm script.
- Coverage: deepens D4 and A2 (pre-trip timing). Whether A2 flips to REDUCES depends on the cycle 24 test. The Drive link is a real action, but do not claim it without checking.

### 3. Embeddable partner widget (owner: `frontend/src/pages/Embed.tsx`, `frontend/src/pages/Judge.tsx` or Settings for the snippet generator)
- Route `#embed?lat&lon&lang`: a stripped, 360 px compact card (Watch level, rain outlook badge, nearest-gauge status, "Open FloodReady" link). No header, no voice, no push prompts.
- The snippet generator offers a copy button for `<iframe src="https://HOST/#embed?lat=..&lon=..&lang=en" width="360" height="420" loading="lazy" title="Flood status">` and a preview. Audiences: libraries, churches, apartment sites.
- Backend/Caddy: change CSP `frame-ancestors` for the `#embed` path only. Keep the rest of the app on `frame-ancestors 'self'`. Check `deploy` Caddyfile headers. Because it is a hash route, the CSP applies to the whole document, so either allow framing app-wide (`frame-ancestors *`) after review, or serve a separate `/embed.html` entry. Choose the separate entry if the review is not finished.
- Rate limits: the embed uses existing GETs. The shared-IP limits were already raised in cycle 17.
- Honest limits: shows the same data and freshness badges, and no personal data is stored.
- Tests: build, browser check at 360 px, iframe load in a local test page with 0 CSP errors.
- Coverage: no row flips. It supports D5 and D3 reach, and the business-case "partner" channel.

### 4. Family plan share link (owner: `frontend/src/components/familyplan/`)
- Encode the plan (household size, medicine/dialysis flags, pets, meeting point, two out-of-area contacts) as compressed base64url in the URL fragment (`#plan=...`). The fragment never reaches a server. Shows a QR via the existing lazy qrcode chunk, a copy-link button, and a print view.
- Import: opening a link shows a "Save this plan" confirmation before writing to device storage. Cap the payload at about 1.5 kB and validate every field (no HTML, strings are rendered as text).
- Privacy: disclose in 5 languages that the link contains the entered names/phones, and that anyone with the link can read it. Default to excluding phone numbers, with a checkbox to include them.
- Coverage: deepens E1 (already REDUCES). It is a memorable demo, "scan to give your sister the plan".
- Tests: encode/decode round-trip, malformed fragment rejected, i18n coverage 0 missing.

## Not recommended now
- METRO, TxDOT, HISD: no verified public feed. A guessed feed would be a fabricated claim. Idea #5 uses link-outs only and must be labeled "official site, not live data in this app".
- Idea #6 text must be sourced only to the verified pages above.
