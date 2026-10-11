# Cycle 37 plan — offline resilience (from cycle-37-research.md)
P0 (done by lead): sw.js — cache.match with ignoreVary; only navigations fall back to the HTML shell. Verified: cold offline reload renders home/settings/prepare/recover/civic/compare/about (7/7) in the prod build.
FRONTEND (P1, ≤1h):
1. Offline safety card (one screen: 911/311/211, Turn Around Don't Drown, the user's last-known risk summary + time, evacuation zone if known, household key needs, family meeting point from the family plan if set) — reachable from the offline banner and Prepare; printable. Sources per research doc (Ready.gov/FEMA URLs).
2. Persist the last generated plan (localStorage) and show it offline with "saved <time>".
3. Ask, Alerts, Drive offline: replace raw errors with a clear offline state ("You're offline — last update <time>" + what still works + link to the safety card); Ask offline offers the canned/knowledge-card answers if available locally, else the safety card.
Strings in src/i18n/p37.ts (5 languages).
