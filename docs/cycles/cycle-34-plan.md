# Cycle 34 plan — one consistent simulated storm (from cycle-34-research.md)
Rule: simulation exists ONLY in demo mode (?demo=1); every simulated item is labelled "Simulated"; real users never see it.

## BACKEND (backend/ excl. app/ai)
- GET `/alerts?lat&lon&simulate=storm` → returns one clearly simulated alert `{event:"Flash Flood Warning", severity:"Severe", headline:"SIMULATED — demo only: Flash Flood Warning for <area>", description:"Simulated storm for demonstration. Not a real NWS alert.", expires:<now+3h>, simulated:true}` plus real alerts; top-level `simulated:true`, `meta.storm_mode:true`.
- `/route-check?simulate=storm`: add top-level `simulated:true`, `meta.storm_mode:true`; message for caution routes must not say "No active flood conditions" when simulated gauges are ≥ minor — say conditions are active (simulated) and name the gauge, like the avoid copy. Keep message_code/params consistent with existing i18n codes (add new code if needed and report it).
- `/risk?simulate=storm`, `/outlook?simulate=storm`, `/watch/status?simulate=storm`: ensure `simulated:true` at top level and `meta.storm_mode:true`.
- Tests (mocked).

## FRONTEND
- Single demo storm flag in shared state (state/place.tsx or a small state/demo.ts; sessionStorage, active only when demo mode is on). One toggle component reused on Home, Alerts, Drive (replace local flags in Watch.tsx and Drive.tsx).
- When on: Home summary/top actions/live conditions fetch /risk, /alerts, /outlook with simulate=storm; Alerts and Drive use it too.
- Any response with `simulated:true` → show "Simulated" tag and hide the "Live · just now" Freshness chip.
- Drive NWS warnings: only show zone-only alerts whose area_desc mentions Harris/Fort Bend/Montgomery/Galveston/Brazoria/Chambers/Liberty/Waller (Houston region) — drop e.g. Corpus Christi.
- New strings in src/i18n/p34.ts (5 languages) if any.
