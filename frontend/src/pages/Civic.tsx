// "Who's responsible" (#civic): officials, flood bond projects and reservoirs.
import { api, type ReservoirPool } from '../api'
import { useApp } from '../ctx'
import { useBk } from '../lib/bk'
import { usePlace, placeName } from '../state/place'
import Report311 from '../components/civic311/Report311'
import WhoToContact from '../components/WhoToContact'
import { useAsync, Warnings } from '../components/ui'
import { Card, ErrorBox, Freshness, PageHeader, RiskBadge, SkeletonCard, SourceLink } from '../components/ds'

const money = (n?: number | null) => (typeof n !== 'number' ? '—' : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : `$${Math.round(n).toLocaleString()}`)

function Contact({ v }: { v?: string | null }) {
  if (!v) return null
  if (/^https?:\/\//i.test(v)) {
    let host = v
    try { host = new URL(v).hostname.replace(/^www\./, '') } catch { /* keep raw */ }
    return <p><SourceLink href={v} label={host} /></p>
  }
  if (/^[\d\s().+-]{7,}$/.test(v)) return <p><a className="text-brand underline" href={'tel:' + v.replace(/[^\d+]/g, '')}>{v}</a></p>
  return <p className="text-muted">{v}</p>
}

function PoolCard({ lat, lon }: { lat: number; lon: number }) {
  const { t, lang } = useApp()
  const pool = useAsync<ReservoirPool>(() => api.reservoirPool({ lat, lon }), [lat, lon])
  const p = pool.data
  if (pool.loading) return <SkeletonCard lines={3} />
  if (pool.error || !p) return null
  const pl = p.pool
  const f1 = (n: number) => n.toFixed(1)
  const rows: [string, number | undefined][] = pl ? [[t('p28.pool.now'), pl.stage_ft], [t('p28.pool.action'), pl.action_ft], [t('p28.pool.minor'), pl.minor_ft], [t('p28.pool.crest').replace('{date}', pl.harvey_crest_date ? new Date(pl.harvey_crest_date + (pl.harvey_crest_date.length === 10 ? 'T12:00:00' : '')).toLocaleDateString(lang, { year: 'numeric', month: 'short', day: 'numeric' }) : ''), pl.harvey_crest_ft]] : []
  const d = p.pool_below_ground_ft
  return (
    <Card title={t('p28.pool.h')}>
      {!pl && <p className="text-muted">{t('p28.pool.off')}</p>}
      {pl && (
        <ul className="space-y-1 text-body-sm">
          {rows.map(([k, v], i) => <li key={i} className={'flex justify-between gap-3' + (i === 0 ? ' font-semibold' : '')}><span>{k}</span><span>{v != null ? <bdi>{f1(v)} {t('p30b.unit.ft')}</bdi> : '—'}</span></li>)}
        </ul>
      )}
      {d != null && <p className="mt-3 text-body-sm">{(d >= 0 ? t('p28.pool.below') : t('p28.pool.above')).replace('{n}', f1(Math.abs(d)))}</p>}
      {p.harvey_above_ground_ft != null && p.harvey_above_ground_ft > 0 && <p className="mt-1 text-body-sm">{t('p28.pool.harvey').replace('{n}', f1(p.harvey_above_ground_ft))}</p>}
      <p className="mt-2 text-caption text-muted">{t('p28.pool.datum')}</p>
      <div className="mt-2"><Freshness meta={p.meta} /> <SourceLink href={p.source || 'https://water.noaa.gov/gauges/ADDT2'} label={t('p28.pool.src')} /></div>
      {p.relevant && <p className="mt-2 text-body-sm"><a className="underline" href="#watch">{t('p28.pool.watch')}</a></p>}
      <p className="mt-2 text-caption text-muted">{t('p28.pool.disc')}</p>
    </Card>
  )
}

export default function Civic() {
  const { t } = useApp()
  const bk = useBk()
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
          <Warnings items={c.warnings} codes={c.warning_codes} />
          <WhoToContact civic={c} />
          <Report311 civic={c} />
          <Card title={t('p5.civic.who')}>
            {resp.length === 0 && <p className="text-body-sm text-muted">{t('rec.na')}</p>}
            <ul className="divide-y divide-line text-body-sm">
              {resp.map((r, i) => (
                <li key={i} className="py-2 first:pt-0"><p className="font-semibold text-ink">{bk(r.code && r.code.replace('civic.resp', 'civic.resp'), {}, r.issue)}</p><p>{bk(r.code ? r.code.replace('civic.resp', 'civic.agency') : null, {}, r.agency)}</p><Contact v={r.contact} /></li>
              ))}
            </ul>
          </Card>
          <Card title={t('p5.civic.bond').replace('{name}', name)}>
            {bondFacts.length === 0 && bondProjects.length === 0 && <p className="text-body-sm text-muted">{t('rec.na')}</p>}
            <ul className="space-y-2 text-body-sm">{bondFacts.map((f, i) => <li key={i}><p>{bk(f.code, f.params, f.text)}</p><SourceLink href={f.source} /></li>)}</ul>
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
            <ul className="mt-3 space-y-2 text-body-sm">{(c.reservoir?.facts ?? []).map((f, i) => <li key={i}><p>{bk(f.code, f.params, f.text)}</p><SourceLink href={f.source} /></li>)}</ul>
          </Card>
          {c.reservoir?.in_area && place && <PoolCard lat={place.lat} lon={place.lon} />}
        </>
      )}
    </div>
  )
}
