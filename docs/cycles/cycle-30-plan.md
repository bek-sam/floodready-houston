# Cycle 30 plan — language equity fixes (from cycle-30-research.md)

| # | Issue | Owner | Fix | Check |
|---|---|---|---|---|
| 1 | Parking result all English (incl. "Call 911") | backend + frontend | parking.py: add `headline_code`, `detail_code`, reason `code` + `params` (keep English text); frontend ParkCard renders t(code, params) with English fallback; keys in p30.ts ×5 langs | es/vi/zh/ar Drive parking result has no English sentences |
| 2 | Widget rain line English | frontend | Widget.tsx uses `outlook.sub.<category>` like Home | /widget?lang=es fully Spanish |
| 3 | Arabic address scrambled | frontend | wrap place labels/addresses in `<bdi>` (place chip, For: line) | ar place chip reads "5300 N Braeswood Blvd" |
| 4 | "Hurricane Harvey" English inside translated chips | frontend | localize the storm name via t('storm.<id>') in sum.exp.gauge / chip.gaugeHist | es chip says "huracán Harvey" |
| 5 | Pool card hardcoded " ft" | frontend | use the existing unit key/formatter (grep 'unit.ft' or ft key) with <bdi> | ar shows number then unit consistently |
| 6-7 | NWS English impacts (disclosed), date/wording nits | frontend (low) | ISO dates → toLocaleDateString(lang); fix zh season/ar CO wording if certain | — |
