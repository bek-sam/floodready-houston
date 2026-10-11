# Cycle 29 plan (freeze 11 AM; each task <=1 h). Source audit: cycle-29-research.md

Owners: D = data/+scripts/+docs/ (not CLAUDE.md) · B = backend/ (not app/ai) · A = backend/app/ai · F = frontend/. One builder per folder.
Order of value for the demo: #2, #1, #6, #3, #8, #4, then the rest.

## Issues

### 1. Demo controls need `?demo=1` (F + D)
Root cause: `frontend/src/state/place.tsx:81-94` only turns demo on via `?demo=1` (sessionStorage); `Drive.tsx:31-33` loads samples only if `demo`; DEMO-DAY.md has 0 mentions.
Decision: do NOT make controls always-on (a real user would see "Simulate storm" and fake Avoid verdicts, which contradicts "not invented facts"). Safer for a live demo: document it AND make it hard to miss.
- D: DEMO-DAY.md: step "Open `BASE/?demo=1`" before pitch step 1 and in "30 minutes before judging" (also `/#judge` sets demoGo: verify it enables demo). Note sessionStorage is per tab: re-open with `?demo=1` after closing the tab.
- F: on Judge page add a one-click "Enter demo mode" button if not already (calls setDemo(true)); in Drive, when `!demo`, no change.
Accept: fresh incognito tab, `/?demo=1#drive` shows sample route chips + Simulate storm switch; a tab without it shows neither.

### 2. 0-inch / stale community report forces caution (B + D)
Root cause: `backend/app/services/route.py:90-104` adds every report <=24h within 100 m as a hazard, even `depth_in == 0` or `kind` outside the enum; any hazard => at least "caution" (line ~138). The row is a test row (kind `street_flooding`, depth 0, id 36805c256ec0, 2026-10-10 22:59 UTC, only report in DB).
Rule: a report counts only if `created_at` <= 6 h old (storm-time freshness; was 24 h), `kind` in {flooded_road, water_over_road, barricade_missing, stalled_vehicles}, and (`depth_in` is None OR `depth_in` > 0). Reports not counting are skipped entirely (no hazard, no count). Keep the high/deep-report rule (>=6 in). Add constant `REPORT_MAX_AGE_H = 6`, `COUNTING_KINDS`.
- B: implement in `recent_reports()` / loop; same filter where Recover lists "Recent reports near Home" (`backend/app/routers/reports.py` GET): hide `depth_in == 0` with no note and unknown kinds. Add pytest: 0-in report -> no hazard; 8-in 1 h old -> counted.
- D (user runs, not me) purge, inspect first:
  `sqlite3 backend/floodready.db "select id,created_at,kind,depth_in,note from reports;"`
  then `sqlite3 backend/floodready.db "delete from reports where depth_in = 0 or kind not in ('flooded_road','water_over_road','barricade_missing','stalled_vehicles');"`
  Do the same on the production DB if deployed. Stop the backend first or accept SQLite lock.
Accept: `UH campus to Downtown` demo route has no "Community report" hazard; `/api/reports` has no 0-in row.

### 3. Civic 6.6 s (B + F + D)
Root cause: skeleton already exists (`Civic.tsx:45`), so the problem is latency and double fetch. `civic.py:46` `get_officials()` makes up to 4 SEQUENTIAL ArcGIS calls (`officials.py:23-37`: precinct, admin, then council); `get_civic` awaits `bond_projects`, `reservoir_status`, `get_officials` one after another; `full_layer` bond layer fetch is cold on first call (`arcgis.py:16`, `ttl=0`). Duplicate request: `useAsync` deps `[place?.lat, place?.lon]` plus WhoToContact/Report311 likely also call `/civic`.
- B: `asyncio.gather` the three in `get_civic`; in `get_officials` run precinct + admin concurrently, council concurrently when `lat/lon` inside Houston bbox (drop the dependency on admin entity, then null it out if admin is not "City of Houston"). Wrap each in `asyncio.wait_for(…, 4)`; on timeout return null for that part. Add `Cache-Control`/in-memory result cache keyed on rounded (lat,lon,3 dp) for 1 h.
- D: add `/civic` (and `/evac`, `/rain24`) for the seeded demo places and Seabrook to `scripts/prewarm.py` PLACES.
- F: dedupe: pass `civic` data down (already passed to WhoToContact/Report311) and grep for any second `api.civic` call (ctx/place hook); memoize in `api.ts` by lat/lon for 60 s.
Accept: second load <300 ms; cold load <2.5 s; one `/api/civic` request in network tab.

### 4. Council "— · C" and raw URLs (B + F + D)
Root cause: `officials.py:36` `(c.get("MEMBER") or "").title()` gives "" when layer has no member; `WhoToContact.tsx:29` falls back to `'—'` and appends `· C`. Raw URLs: `data/civic.json` responsibility[].contact are bare URLs rendered as text in `Civic.tsx:60` (`<p className="text-muted">{r.contact}</p>`).
- B: in officials, set `member=None` when empty; keep `district`.
- F: WhoToContact: if no name and role==='council' render `Council District {district}` (add i18n key `c11.who.district`); if no name at all hide the row unless phone/url exists. Civic.tsx: if `r.contact` matches `^https?://` render `<SourceLink href={r.contact} label={host}/>` (hostname without www) else tel/text; if matches phone pattern render `tel:` link.
- D: no data change required (contact strings fine as URLs).
Accept: Meyerland-area/77096 address shows "Council District C" (or a name), never "—"; no bare `https://` text in Who handles what.

### 5. Drive verdict below the fold on mobile (F)
Root cause: scroll exists (`Drive.tsx:93` `head.current?.scrollIntoView` after 50 ms) but runs before the verdict card renders when `busy` skeleton swaps in (head ref null) and is skipped on cached/sample path; the form, ParkCard (line 134) and DemoPanel precede it.
- F: replace the timeout with a `useEffect` on `[res, busy]` that scrolls `head.current` when `!busy && res`; add `scroll-mt-16` class on the verdict Card. Move `ParkCard` below the verdict (after result) so form -> result are adjacent.
Accept: at 390x844, tap Check route -> "Avoid" badge in viewport within 1 s, for typed and sample routes.

### 6. Avoid message / long USACE crossing names (D + B + F)
Root cause: data, not code: `data/crossings.geojson` has 25+ features (x085, x102-x120 etc.) whose `name` is the raw USGS description ("Harvey high-water mark: USACE Water-Surface measure point at Hwy 6 bridge at Buffalo Bayou. Water-surface elevations were made on selected days by the USACE during 9/9/17 through 9/16/2017"). `route.py:85` copies `name`; message joins first 3 (`route.py:135`) and frontend `routeMessage` (`lib/bk.ts:44`) does the same.
- D: add `short_name` to every crossing (script `scripts/` regen): strip text after first ". ", strip "USACE Water-Surface measure point at", cap 60 chars -> e.g. "Hwy 6 bridge at Buffalo Bayou (Harvey high-water mark)". Keep full text in `reasons[]`/`properties.description`. Keep `name` for compatibility.
- B: use `p.get("short_name") or p.get("name")` for hazard `name` and message; cap list to 3 and append "+N more".
- F: `hazards` list: `truncate` any name >80 chars defensively; `routeMessage` cap 3 names + "+N more".
Accept: demo Allen Parkway avoid message < 300 chars, no "Water-surface elevations", no name > 80 chars (add a pytest/eyeball over crossings.geojson).

### 7. Compare 13 s (B + D + F)
Root cause: `loadCol` (`components/compare/useCompare.ts:16-19`) runs risk+evac+crossings in parallel, THEN floodHistory + zipInsurance serially after; `/flood-history` and `/zip-insurance` took 13 s cold for Seabrook (OpenFEMA/USGS remote calls, no prewarm; per-point cache miss). Seabrook not in `prewarm.py`. "No data" Harvey not explained.
- D: prewarm: add Seabrook (29.564,-95.025, ZIP 77586) for /risk /flood-history /zip-insurance/evac; also add ZIP 77586.
- B: `/flood-history` and `/zip-insurance`: add 24 h disk cache by (rounded lat/lon, zip) and per-call timeout 8 s returning partial with warning rather than blocking; confirm OpenFEMA call uses limited `$select`/`$filter` (profile with `time curl`).
- F: in `loadCol` start history/zip in the same `Promise.all` as risk (zip from label is already known before); render each column progressively (set col as soon as risk arrives, fill others). In CompareTable, Harvey "No data" -> "No Harvey extent data here (layer covers City of Houston only), not the same as 'did not flood'".
Accept: warm Seabrook column <3 s; cold <8 s with progressive fill; explanatory text visible.

### 8. Ask citations (A + F)
Root cause: `ai/graph.py:555-557` builds `sources` only from URLs that appear in the model's answer text, falling back to `sorted(allowed)[:3]` (retrieved RAG chunks = blogs). Tool-result URLs (`_tool_sources`, `graph.py:522`) are used only as a filter, never prepended, so FEMA NFHL/City of Houston never show. Glued markers: `MessageList.tsx:13-24` renders `<sup>` badges with `ms-0.5` and no brackets, so `[3][2]` reads "32".
- A: `sources = ordered(tool_sources first (official: fema.gov, houstontx.gov, noaa.gov, weather.gov, usgs.gov, hcfcd.org, fema `msc`), then found, then allowed)` dedupe, cap 5; when answer has no `[n]` markers for tool-derived facts, append `[k]` for the tool source to the sentence containing "Zone"/"Harvey"/"ft". Down-rank non-official domains (blogs, news) when an official tool source exists. Preserve `citations.attach` index validity (it drops out-of-range markers: reorder before attach). Add eval question to `data/eval/questions.jsonl` (D) "Is my address in a flood zone?" expecting a fema/houstontx source.
- F: render marker as `[n]` with `me-0.5` and thin space (e.g. `<sup>[{n}]</sup>`), so adjacent markers read "[3][2]"; show the host label in the Sources list for tool sources ("FEMA NFHL", "City of Houston Harvey layer") via a host->label map.
Accept: the flood-zone question shows FEMA + City sources first; text has "[1][2]" not "12".

### 9-13 (low priority; do only if time)
9. F: Replay gauge list label "At this moment" vs "Peak (45.66 ft)" under the chart; one number defined as peak.
10. F: verify bottom-nav padding (`pb-24` on main); likely screenshot artifact.
11. F: Alerts push copy: distinguish `Notification.permission === 'default'` vs `'denied'`; denied gets "Enable in browser settings: lock icon -> Notifications".
12. F: Replay gauge list: sort nearest-to-place first, pin it.
13. F: leave onboarding; add "Skip, enter address" link on step 1.

## Judge-wow gaps (cheapest fix each)
1. Instant first 10 s: D runbook `?demo=1` line + prewarm civic/compare/Seabrook (issues 1, 3, 7); F issue 5 auto-scroll. No new feature.
2. Clean Avoid beat: issues 2 and 6 (purge test report, short names) plus message template "Avoid: N named crossings + <gauge> in <status> flooding" (B: reuse `conds` already built in `route.py:119-130`; F: map `fitBounds` to hazards and pulse hazard markers).
3. Visible grounding: issue 8 (tool sources first, labeled "FEMA NFHL" / "City of Houston").

## Folder assignments (one builder each)
- D (data/ scripts/ docs/): DEMO-DAY.md, short_name regen, prewarm additions, eval question, run purge SQL with user approval.
- B (backend, not app/ai): route.py report rule + short_name, reports router filter, civic/officials parallel + cache, flood-history/zip caching, tests.
- A (backend/app/ai): graph.py source ordering/labels.
- F (frontend): Judge demo button, Drive scroll + ParkCard order, WhoToContact/Civic rendering, Compare progressive load + Harvey copy, MessageList `[n]` markers, items 9-13.
Cross-dependency: F's short-name use is defensive; B/D can land independently. Run `scripts/demo_check.py BASE --front` (21/21) after all merges, before 10:30 AM.
