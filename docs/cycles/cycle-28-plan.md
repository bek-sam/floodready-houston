# Cycle 28 plan (freeze 11:00 AM CDT; each item <=1.5h)

Inputs: `docs/cycles/cycle-28-research.md`, CLAUDE.md, code read of `services/zipinsurance.py`, `services/risk.py`, `services/civic.py`, `routers/buyouts.py`, `frontend/src/pages/Civic.tsx`, `components/RentBuy.tsx`.

## 1. F2 Addicks pool vs this address's ground (backend + frontend, 1.5h)
**Placement:** new endpoint `GET /api/reservoir/pool?lat&lon`, shown as a new card in `Civic.tsx` directly under the existing reservoir card (`p5.civic.reservoir`), and only when `/civic reservoir.in_area` is true (also usable by Watch later). Do NOT change `/risk` (keeps its contract and latency). New files: `backend/app/services/reservoir.py`, `backend/app/routers/reservoir.py` (backend agent includes router in main.py). No AI folder changes.

**Source:** `GET https://api.water.noaa.gov/nwps/v1/gauges/ADDT2` -> `status.observed.primary` (pool ft), `validTime`, `flood.categories.action.stage` (93), `minor.stage` (96), historic crest 109.09 on 2017-08-30. Use `services/http.get_json` with ttl 300 (90-180 s in storm mode, per freshness). Pool stage here is elevation above sea level (gauge-bottom 67.8 ft matches the Addicks floor); the datum is likely NGVD29 while `/risk elevation_ft` (EPQS) is NAVD88, so label it approximate.
**Barker:** NWPS `BRKT2` returns "could not find gauge ID" (tested). Do not invent a Barker gauge. Return `barker: null`; Barker stays area-flag only (existing Fort Bend polygon).

**Response (exact):**
```
{ "available": bool,
  "pool": {"gauge_id":"ADDT2","name":"Addicks Reservoir pool","stage_ft":83.89,"observed_at":"ISO","action_ft":93,"minor_ft":96,"harvey_crest_ft":109.09,"harvey_crest_date":"2017-08-30","status":"normal|action|minor|unknown"} | null,
  "ground_elevation_ft": float|null,      // from risk service (reuse the cached elevation call, not a new source)
  "pool_below_ground_ft": float|null,     // ground - stage_ft
  "harvey_above_ground_ft": float|null,   // 109.09 - ground
  "relevant": bool,                       // in_area (addicks_approx or barker) AND ground within 15 ft above current pool, or pool>=action
  "message": str, "message_code": "res.pool.*",
  "datum_note": "Pool and ground elevations may use different vertical datums (NGVD29 vs NAVD88); treat as approximate.",
  "disclaimer": "Not official guidance. Call 911 and follow evacuation orders.",
  "barker": null, "source": "https://water.noaa.gov/gauges/ADDT2",
  "meta": {as_of, source, freshness, storm_mode}, "warnings"?: [] }
```
Fallback: NWPS fail -> `available:false`, pool null, message "Live pool level unavailable", fall back to `data/gauges.json` flood stages only (static thresholds, freshness "snapshot"). Never crash; elevation None -> no comparison lines. Tests: pytest with mocked get_json (normal, no elevation, upstream fail).
**Frontend:** card with a vertical gauge or simple three-row list (pool now / action 93 / minor 96 / Harvey crest 109.09), the "pool is X ft below your ground; Harvey peaked Y ft above it" line when numbers exist, Freshness chip, SourceLink, disclaimer, i18n keys in a new `i18n/p28.ts` (en/es/vi; fall back to en). Add `api.reservoirPool` in `api.ts` and wire a "Watch this" prompt linking to #watch only if `relevant`.
**Coverage:** F2 -> REDUCES. F1 stays INFORMS (dam condition is structural).

## 2. E3 tenant relocation-rights card (frontend 0.75h + data 0.25h)
**Placement:** inside `RentBuy.tsx` buyout block (renter branch, shown when `buy.in_buyout_area === true`, plus a collapsed "if you rent" note otherwise). No new endpoint.
**Accurate wording (required):** "If a buyout or acquisition uses federal money (for example FEMA or HUD funds), tenants who are displaced may be entitled to relocation help under the Uniform Relocation Act (49 CFR Part 24): advance written notice, advisory services and, if you qualify, moving and rent-replacement payments. This does not apply to purely local or voluntary programs without federal funds, and eligibility depends on the specific program. Ask the program in writing whether federal funds are used. This is not legal advice." Do NOT say tenants are always entitled; do NOT promise amounts. Include a copy-able letter asking (1) whether federal funds are involved, (2) for the written general information notice, (3) for relocation advisory services and eligibility determination; plus "keep your lease and rent receipts".
**Sources:** `https://www.ecfr.gov/current/title-49/subtitle-A/part-24` (data agent to curl-verify the URL returns 200; research tested the versioner API for 24.2 "Displaced person") and the county page `https://hcd.harriscountytx.gov/Disaster-Recovery/Buyout-Relocation-Programs/` (data agent to re-fetch once, because research did not). Add knowledge card section to `data/knowledge/renters-and-buyouts.md` so /ask can cite it. Mark card "not official guidance."
**Coverage:** E3 -> REDUCES.

## 3. E5 FAA airport line (backend 1h, frontend 0.25h) -- DO ONLY IF F2 and E3 land by 9:30
`GET /api/airports/status` -> `{airports:[{code:"IAH"|"HOU", closed:bool, reason:str|null, reopen:str|null}], source:"https://nasstatus.faa.gov/", meta, warnings?}`. Parse the XML from `https://nasstatus.faa.gov/api/airport-status-information` (stdlib `xml.etree`, filter `ARPT in {IAH,HOU}` inside `Airport_Closure_List`); ttl 120. Copy: "FAA reports closed" / "FAA does not report a closure" (not "open"; the feed is NAS closures only, not weather or delays). Failure -> `closed:null`, "status unavailable". Show one line on the Drive page. E5 stays INFORMS (partial credit). Skip if time is short.

## 4. Bugs and verification
- **OpenFEMA policies / Oct 15:** VERIFIED no v2 dependency. `services/zipinsurance.py` `_policies` and `_premiums` already call `v3/NfipPolicies` (curl today returns `entityname:NfipPolicies, version:v3` with rows for 77096). Claims use v3 first with v2 fallback (fine; v2 fallback just returns None after removal). No endpoint fix needed.
- **Bug (cache poisoning, fix in backend, 0.25h):** `fetch_zip` stores a result with `premiums:None` and `policies_in_force:None` when only the policy calls transiently fail; it is then cached 24 h in memory and on disk, so one blip hides premiums all day. Fix: only `_mem`/`diskcache.put` when claims succeeded AND (premiums or policies_in_force) is not None, otherwise return the result with a `warnings` entry and a short TTL (5 min). Also the disk-snapshot check `"premiums" in snap` accepts a None premium snapshot; require `snap.get("premiums") is not None` or fall through to fetch.
- **Bug (minor):** `_policies` uses `$inlinecount` count of records active today; metadata `count` is 0 when the query returns none, mapped to None (correct); `_premiums` caps at 10000 rows (large ZIPs such as 77096 may exceed it; `sample_size` then silently equals 10000). Fix: add a note/`truncated:true` when 10000 rows returned.
- **Source URLs:** `SOURCE` in the module is claims v3; premiums carry the policies-v3 URL (good).
- **D7 hygiene:** `grep waterservices` over backend/app and scripts returned no code hits (no migration needed); data agent re-confirm in `scripts/` only.
- **A9 re-verification (for coverage doc):** code read shows `/parking/check` (`routers/parking.py`, `services/parking.py`) and `/rain24` (`routers/rain24.py`) exist, and `frontend/src/components/rain24/RainCard.tsx` and `pages/Home.tsx` reference them, so a move-your-car action exists -> count A9 as REDUCES (34). Docs agent: update coverage doc; confirm in the UI by loading Home with a test address.
- **Not claimed:** D7, D6, C5, F1, B4/B5 stay structural/INFORMS. F3 and C4 not built today. Realistic total after this cycle: 36/52 (A9, F2, E3); E5 stays INFORMS.

## 5. Builder assignments (one per folder)
- **data/ + scripts/ + docs/ builder:** curl-verify eCFR part-24 and county buyout URLs; add the tenant-rights section to `data/knowledge/renters-and-buyouts.md` with those sources; add `data/knowledge` pool note to `reservoirs-and-dams.md` (thresholds 93/96, Harvey crest 109.09 with NWPS source); confirm no `waterservices` in scripts; write the `docs/cycles/cycle-28-coverage.md` recount (A9, F2, E3). Done by 8:30.
- **backend/ (excluding app/ai) builder:** order: (1) `/reservoir/pool` + tests, (2) zipinsurance cache fix + truncated flag + test, (3) `/airports/status` if time. Register routers in `main.py`. Done by 9:45.
- **frontend/ builder:** (1) Civic pool card + `api.reservoirPool` + i18n `p28.ts`, (2) E3 card in `RentBuy.tsx` (copy above, can start immediately, no backend dependency), (3) Drive airport line if endpoint ships. Typecheck/build must pass. Done by 10:15.
- **AI agent:** none (optional: re-run `scripts/eval_ai.py` after knowledge-card edits; not required).
