# Cycle 31 plan — a11y + perf (from cycle-31-research.md)
Owner: frontend only.
1. Serious: About dark-mode contrast (About.tsx:31 white on bg-brand 2.21:1) → use a token pair that passes 4.5:1 in both themes.
2. Moderate: `region` — wrap EmergencyStrip in a landmark (e.g. <aside aria-label> or inside <header>/<nav> role) and onboarding content in <main>.
3. Moderate: heading-order at 390 px on 7 routes — fix h3-after-h1 (promote section titles to h2 or make Card titles configurable) without visual change.
4. Skip link: focus-on-load to <main> should not make the skip link unreachable — keep skip link first in tab order (e.g. don't auto-focus main on first load, only on route change).
5. Perf (only if low-risk): code-split heavy route pages with React.lazy + Suspense (keep Home eager); report main chunk before/after.
Acceptance: axe 0 serious on all routes in light/dark; build passes; 0 page errors; main chunk smaller.
