import { useEffect, useState } from 'react'
import { api, type SourceHealth, type StatusReport } from '../api'
import { useApp } from '../ctx'
import { Card, ErrorBox, Freshness, LoadingText, PageHeader, RiskBadge } from '../components/ds'
import type { Level } from '../lib/levels'

const LEVEL: Record<SourceHealth['circuit'], Level> = { closed: 'normal', half_open: 'watch', open: 'warning', unknown: 'unknown', unconfigured: 'unknown', not_used: 'unknown' }
const circuitOf = (s: SourceHealth): SourceHealth['circuit'] => (s.circuit === 'closed' && !s.last_success ? 'not_used' : s.circuit)
const SNAP_KEYS = ['crossings', 'harvey', 'dialysis', 'shelters', 'civic', 'knowledge']

export default function Status() {
  const { t, lang } = useApp()
  const [data, setData] = useState<StatusReport | null>(null)
  const [failed, setFailed] = useState(false)
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    let alive = true
    api.status().then((d) => { if (alive) { setData(d); setFailed(false) } }).catch(() => { if (alive) setFailed(true) })
    // The server probes in the background, so a second read a few seconds later shows fresh results.
    const id = setTimeout(() => { if (alive) setNonce((n) => n + 1) }, nonce === 0 ? 6000 : 1e9)
    return () => { alive = false; clearTimeout(id) }
  }, [nonce])

  const when = (iso: string | null) => {
    if (!iso) return t('p9.status.never')
    const d = Date.parse(iso)
    return Number.isFinite(d) ? new Date(d).toLocaleTimeString(lang, { hour: 'numeric', minute: '2-digit' }) : '—'
  }
  const day = (iso: string | null | undefined) => {
    const d = iso ? Date.parse(iso + 'T00:00:00Z') : NaN
    return Number.isFinite(d) ? new Intl.DateTimeFormat(lang, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(d) : t('p9.status.unknownDate')
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t('p9.status.title')} subtitle={t('p9.status.sub')} />
      {failed && !data && <ErrorBox error={t('p9.status.fail')} onRetry={() => setNonce((n) => n + 1)} />}
      {!data && !failed && <LoadingText />}
      {data && (
        <>
          <div className="flex flex-wrap items-center gap-2"><Freshness meta={data.meta} />{data.storm_mode && <span className="text-body-sm text-watch">{t('p9.status.storm')}</span>}</div>
          <Card title={t('p9.status.sources')}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-body-sm">
                <thead className="text-caption text-muted">
                  <tr><th className="py-2 pe-3 font-medium">{t('p9.status.col.source')}</th><th className="pe-3 font-medium">{t('p9.status.col.state')}</th>
                    <th className="pe-3 font-medium">{t('p9.status.col.ok')}</th><th className="pe-3 font-medium">{t('p9.status.col.err')}</th><th className="font-medium">{t('p9.status.col.p50')}</th></tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data.sources.map((s) => (
                    <tr key={s.name} data-testid="status-row">
                      <td className="py-2 pe-3 font-medium text-ink">{s.name}</td>
                      <td className="pe-3"><RiskBadge level={LEVEL[circuitOf(s)] ?? 'unknown'} size="sm" label={t('p9.status.circuit.' + circuitOf(s))} /></td>
                      <td className="pe-3 tabular-nums text-muted">{when(s.last_success)}</td>
                      <td className="pe-3 tabular-nums text-muted">{s.last_error ? when(s.last_error) : '—'}</td>
                      <td className="tabular-nums text-muted">{s.p50_ms != null ? `${s.p50_ms} ms` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <Card title={t('p9.status.snapshots')}>
            <ul className="divide-y divide-line">
              {SNAP_KEYS.filter((k) => k in data.snapshots).map((k) => (
                <li key={k} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                  <span className="text-body-sm text-ink">{t('p9.status.snap.' + k)}</span>
                  <span className="text-body-sm tabular-nums text-muted">{day(data.snapshots[k])}</span>
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
