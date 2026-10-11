# Fix plan from the problem-by-problem audit (verify-AB/CD/EFG.md)
Feature freeze 11 AM: these are fixes to make existing features truthful and safe.

## BACKEND (backend/ excl. app/ai)
1. Route safety (verify-AB #1, #2): a single community report may raise a route to at most "caution"; "avoid" from reports needs ≥2 reports (distinct ids) or a crossing+conditions as today. If an active NWS Flood/Flash Flood Warning polygon (services used by /alerts/area) intersects the route line → at least "caution" with a message naming the warning; never "safe"/"no known" wording under an active warning. Keep message codes (add new codes if needed, report them).
2. Parking (verify-AB #3): inside the Addicks/Barker reservoir area (existing buyout/reservoir checks in civic/reservoir services) add a reason (code + English text) and verdict "move" when the pool is at/above action stage or simulate=storm; otherwise add an informational reason.
3. low_ground (verify-AB #5): either compute it honestly (e.g. elevation below nearest gauge flood stage is NOT valid — prefer: drop the field from responses or set from a documented rule) — choose the honest minimum: remove it from UI-facing use and document; do not invent a rule.
4. SMS ALERTS ON (verify-CD #1): Twilio isn't configured, so no SMS alerts are sent. Change the "on" reply to say the sign-up is saved and alerts will be texted once the SMS service is connected (en/es/vi) — and if TWILIO_* is configured, actually send the watch-level-rise SMS from the existing 5-min loop (reuse push loop logic). (verify-CD #5) address replies must suggest "ALERTS ON <their ZIP or address>" not 77096.
5. ZIP insurance policies_in_force null (verify-CD #3): fix the OpenFEMA policies query/aggregation for 77586/77004/77026/77477 (compare with OpenFEMA count 4,980 for 77586); add a mocked test.
6. Push retry (verify-CD #2): failed sends retried next loop (don't mark level as sent unless delivered); 410/404 gone subscriptions removed.
7. /watch outside region (verify-CD #6): reject (422) places outside the Houston region bbox used elsewhere.
Tests mocked; pytest green.

## DATA (data/ + scripts/)
8. Crossings (verify-AB #4): fix x126 label ("gulf of Mexico") and x119 Fannin St. coordinates using the cited source; re-run short_name script; validate JSON.

## FRONTEND
9. (verify-EFG #1) In a warning, households with no car / dialysis / oxygen / power device / wheelchair must get the "help to evacuate" action (STEAR / 211 / call 911) in Top actions — not "check your route before you drive" (lib/summary.ts ~228-238).
10. (verify-EFG #2) Recover page: add post-flood electrical/floodwater safety (downed lines, don't enter flooded rooms with power on, floodwater contamination) from the existing data/knowledge/post-flood-safety.md sources.
11. (verify-EFG #5) Medical note localized (es/vi/zh/ar) — no English leftovers.
12. (verify-EFG #6) Seabrook/other cities: civic copy must not say Houston/unincorporated for places in another city — use jurisdiction from /risk.
13. (verify-CD #4) ZIP insurance card: when the place label has no ZIP, use the place's stored zip or reverse geocode result; otherwise show "Add a ZIP" input.
14. Low_ground: hide any UI that depends on it if backend drops it.
Strings in src/i18n/p39.ts (5 languages).
