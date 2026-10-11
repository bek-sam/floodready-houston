import { Clock, Database, History, Radio, Zap } from 'lucide-react'
import type { GaugeFlags, Meta } from '../../api'
import { useApp } from '../../ctx'

const ICON = { stale: Clock, live: Radio, recent: Clock, cached: Clock, snapshot: Database, historical: History } as const

function ago(t: (k: string) => string, iso: string): string {
  const ms = Date.now() - Date.parse(iso)
  if (!Number.isFinite(ms) || ms < 60_000) return t('p9.fresh.ago.now')
  const min = Math.round(ms / 60_000)
  if (min < 90) return t('p9.fresh.ago.min').replace('{n}', String(min))
  const hr = Math.round(min / 60)
  if (hr < 48) return t('p9.fresh.ago.hr').replace('{n}', String(hr))
  return t('p9.fresh.ago.day').replace('{n}', String(Math.round(hr / 24)))
}

export function freshnessLabel(m: Pick<Meta, 'freshness' | 'as_of' | 'snapshot_date'>, t: (k: string) => string, lang: string): string {
  let fk: string = m.freshness
  if (fk === 'live' || fk === 'recent' || fk === 'cached') {
    const min = (Date.now() - Date.parse(m.as_of)) / 60_000
    if (Number.isFinite(min)) fk = min <= 15 ? 'live' : min <= 120 ? 'recent' : 'stale'
  }
  const kind = t('p9.fresh.' + fk)
  const d = m.snapshot_date || m.as_of
  const when = Date.parse(d)
  if (m.freshness === 'historical') return Number.isFinite(when) ? `${kind} · ${new Date(when).getUTCFullYear()}` : kind
  if (m.freshness === 'snapshot') {
    if (!Number.isFinite(when)) return kind
    return `${kind} · ${new Intl.DateTimeFormat(lang, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(when)}`
  }
  return `${kind} · ${ago(t, m.as_of)}`
}

/** "Live · 2 min ago" / "Snapshot · Oct 10, 2026" / "Historical · 2017" badge from a response `meta`. Renders nothing without meta. */
export function Freshness({ meta, className = '', prefix }: { meta?: Meta | null; className?: string; prefix?: string }) {
  const { t, lang } = useApp()
  if (!meta || !meta.freshness) return null
  const Icon = ICON[meta.freshness] ?? Clock
  const label = (prefix ? prefix + ' · ' : '') + freshnessLabel(meta, t, lang)
  return (
    <span className={`inline-flex flex-wrap items-center gap-x-2 text-caption text-muted ${className}`}>
      <span data-testid="freshness" aria-label={t('p9.fresh.aria').replace('{label}', label)} title={meta.source}
        className="inline-flex items-center gap-1 whitespace-nowrap rounded-full border border-line bg-surface-2/60 px-2 py-0.5">
        <Icon aria-hidden size={12} className="shrink-0" />{label}
      </span>
      {meta.storm_mode && (
        <span className="inline-flex items-center gap-1 whitespace-nowrap text-watch font-semibold"><Zap aria-hidden size={12} />{t('p9.fresh.storm')}</span>
      )}
    </span>
  )
}

/** "Stale" / "Provisional" / "Gauge offline" / "Unusual jump" chips for a gauge. */
export function GaugeChips({ g, className = '' }: { g: GaugeFlags; className?: string }) {
  const { t } = useApp()
  const chips: [string, string][] = []
  if (g.offline) chips.push(['offline', 'p9.chip.offline'])
  else if (g.stale) chips.push(['stale', 'p9.chip.stale'])
  if (g.spike) chips.push(['spike', 'p9.chip.spike'])
  if (g.provisional && !g.offline) chips.push(['provisional', 'p9.chip.provisional'])
  if (!chips.length) return null
  return (
    <span className={`inline-flex flex-wrap gap-1 ${className}`}>
      {chips.map(([k, key]) => (
        <span key={k} title={t(key + '.d')} className="inline-flex items-center rounded-full border border-line bg-surface-2 px-2 py-0.5 text-caption font-medium text-ink">
          {t(key)}
        </span>
      ))}
    </span>
  )
}
