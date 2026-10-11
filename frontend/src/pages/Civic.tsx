// "Who's responsible" (#civic): officials, flood bond projects and reservoirs.
import { api } from '../api'
import { useApp } from '../ctx'
import { usePlace, placeName } from '../state/place'
import Report311 from '../components/civic311/Report311'
import WhoToContact from '../components/WhoToContact'
import { useAsync, Warnings } from '../components/ui'
import { Card, ErrorBox, PageHeader, RiskBadge, SkeletonCard, SourceLink } from '../components/ds'

const money = (n?: number | null) => (typeof n !== 'number' ? '—' : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : `$${Math.round(n).toLocaleString()}`)

export default function Civic() {
  const { t } = useApp()
  const { place } = usePlace()
  const civic = useAsync(() => api.civic(place), [place?.lat, place?.lon])
  const name = place ? placeName(place.nickname, t) : 'Houston'
  const c = civic.data
  const bondFacts = c?.bond?.facts ?? []
  const bondProjects = c?.bond?.projects ?? []
  const resp = c?.responsibility ?? []

  return (
    <div className="space-y-4">
      <PageHeader title={t('p5.civic.title')} subtitle={t('p5.civic.sub')} forPlace />
      {civic.loading && <div className="space-y-4" aria-busy="true"><SkeletonCard lines={4} /><SkeletonCard lines={4} /><SkeletonCard lines={3} /></div>}
      {civic.error && <ErrorBox error={civic.error} onRetry={civic.reload} />}
      {c && (
        <>
          <Warnings items={c.warnings} />
          <WhoToContact civic={c} />
          <Report311 civic={c} />
          <Card title={t('p5.civic.who')}>
            {resp.length === 0 && <p className="text-body-sm text-muted">{t('rec.na')}</p>}
            <ul className="divide-y divide-line text-body-sm">
              {resp.map((r, i) => (
                <li key={i} className="py-2 first:pt-0"><p className="font-semibold text-ink">{r.issue}</p><p>{r.agency}</p><p className="text-muted">{r.contact}</p></li>
              ))}
            </ul>
          </Card>
          <Card title={t('p5.civic.bond').replace('{name}', name)}>
            {bondFacts.length === 0 && bondProjects.length === 0 && <p className="text-body-sm text-muted">{t('rec.na')}</p>}
            <ul className="space-y-2 text-body-sm">{bondFacts.map((f, i) => <li key={i}><p>{f.text}</p><SourceLink href={f.source} /></li>)}</ul>
            {bondProjects.length > 0 && (
              <ul className="mt-3 divide-y divide-line">
                {bondProjects.map((p, i) => {
                  const pct = p.budgeted && p.spent != null ? Math.min(100, (p.spent / p.budgeted) * 100) : null
                  return (
                    <li key={i} className="py-3 text-body-sm">
                      <p className="font-semibold text-ink">{p.name}</p>
                      <p className="mt-1 flex flex-wrap items-center gap-2 text-muted">
                        {p.status && <span className="rounded-full border border-line bg-surface-2 px-2 text-caption font-semibold text-ink">{p.status}</span>}
                        {typeof p.distance_mi === 'number' && <span>{t('p5.civic.away').replace('{mi}', p.distance_mi.toFixed(1))}</span>}
                      </p>
                      {pct != null && (
                        <div className="mt-2">
                          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2" role="img" aria-label={t('p5.civic.spent').replace('{spent}', money(p.spent)).replace('{budget}', money(p.budgeted))}>
                            <div className="h-full rounded-full bg-water" style={{ width: `${pct}%` }} />
                          </div>
                          <p className="mt-0.5 text-caption text-muted">{t('p5.civic.spent').replace('{spent}', money(p.spent)).replace('{budget}', money(p.budgeted))}</p>
                        </div>
                      )}
                      {p.url && <SourceLink href={p.url} />}
                    </li>
                  )
                })}
              </ul>
            )}
          </Card>
          <Card title={t('p5.civic.reservoir')}>
            <RiskBadge level={c.reservoir?.in_area ? 'warning' : 'normal'} label={c.reservoir?.in_area ? t('rec.inReservoir') : t('rec.notReservoir')} />
            <ul className="mt-3 space-y-2 text-body-sm">{(c.reservoir?.facts ?? []).map((f, i) => <li key={i}><p>{f.text}</p><SourceLink href={f.source} /></li>)}</ul>
          </Card>
        </>
      )}
    </div>
  )
}
