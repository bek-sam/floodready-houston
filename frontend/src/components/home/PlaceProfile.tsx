import { useEffect, useState, type ReactNode } from 'react'
import { apiC20, type FloodHistory, type Nri, type Risk } from '../../api'
import { useApp } from '../../ctx'
import { fill, NOAA_GAUGE, SRC } from '../../lib/summary'
import { coded, useBk } from '../../lib/bk'
import { SourceLink, StatusBadge } from '../ds'

function Row({ k, children }: { k: string; children: ReactNode }) {
  return (
    <div className="grid gap-1 py-3 first:pt-0 sm:grid-cols-[200px_1fr] sm:gap-4">
      <dt className="text-body-sm font-semibold text-muted">{k}</dt>
      <dd className="min-w-0 text-body-sm text-ink">{children}</dd>
    </div>
  )
}

/** FEMA National Risk Index chip for the census tract. Hidden when unavailable. */
function NeighborhoodChip({ lat, lon }: { lat: number; lon: number }) {
  const { t } = useApp()
  const [n, setN] = useState<Nri | null>(null)
  useEffect(() => {
    let live = true
    setN(null)
    if (Number.isFinite(lat) && Number.isFinite(lon)) apiC20.nri({ lat, lon }).then((x) => { if (live) setN(x) }).catch(() => {})
    return () => { live = false }
  }, [lat, lon])
  if (!n || n.available === false) return null
  const rate = (v?: string | null) => {
    const key = 'p26.nri.r.' + (v ?? '').toLowerCase().replace(/[^a-z]/g, '')
    const txt = t(key)
    return v && txt !== key ? txt : t('p26.nri.r.na')
  }
  const parts = [
    n.inland_flood && fill(t, 'p26.nri.flood', { v: rate(n.inland_flood.rating) }),
    n.resilience && fill(t, 'p26.nri.resl', { v: rate(n.resilience.rating) }),
    n.social_vulnerability && fill(t, 'p26.nri.sovi', { v: rate(n.social_vulnerability.rating) }),
  ].filter(Boolean) as string[]
  if (!parts.length) return null
  return (
    <section className="rounded-md border border-line bg-surface-2 p-3">
      <h4 className="text-body-sm font-semibold text-ink">{t('p26.nri.title')}</h4>
      <p className="mt-1 text-body-sm text-ink">{parts.join(' · ')}<SourceLink href={n.source || 'https://hazards.fema.gov/nri/'} label={t('p26.nri.src')} /></p>
      <p className="mt-1 text-caption text-muted">{t('p26.nri.note')}</p>
    </section>
  )
}

/** "Your place's flood profile": key facts as a key-value list + what the FEMA map misses. */
export function PlaceProfile({ r, loc }: { r: Risk; loc?: { lat: number; lon: number } | null }) {
  const { t } = useApp()
  const bk = useBk()
  const approx = r.elevation_source === 'open_meteo_approx'
  const facts = (Array.isArray(r.facts) ? r.facts : []).filter((f) => f && f.text)
  const yn = (v: boolean | null | undefined) => (v === true ? t('prof.yes') : v === false ? t('prof.no') : t('prof.unknown'))
  return (
    <div className="space-y-5">
      <dl className="divide-y divide-line">
        <Row k={t('prof.zone')}>
          <span className="font-semibold">{r.fema_zone ? fill(t, 'chip.fema', { zone: r.fema_zone }) : '—'}</span>
          {r.zone_subtype && <span className="text-muted"> · {r.zone_subtype}</span>}
          <span className="mt-1 block">{t(r.sfha ? 'home.femaPlain.sfha' : 'home.femaPlain.low')}
            <SourceLink href={r.sfha ? SRC.sfha : SRC.notSfha} label={r.sfha ? '12 CFR 339 App. A' : undefined} /></span>
        </Row>
        <Row k={t('prof.harvey')}>
          {r.harvey?.flooded === true ? t('prof.harveyIn') : r.harvey?.flooded === false ? t('prof.harveyOut') : t('prof.harveyNone')}
          {r.harvey?.note && <span className="mt-1 block text-caption text-muted">{bk(r.harvey.note_code, {}, r.harvey.note)}</span>}
          <SourceLink href={r.harvey?.source} />
        </Row>
        <Row k={t('prof.elev')}>
          <span className="tabular-nums">{r.elevation_ft != null ? `${approx ? t('c6.approx') + ' ' : ''}${Math.round(r.elevation_ft)} ft` : '—'}</span>
          {r.elevation_ft != null && approx && <span className="block text-caption text-muted">{t('c6.approxNote')}</span>}
          {r.elevation_ft != null && (approx
            ? <SourceLink href="https://open-meteo.com/en/docs/elevation-api" label="Open-Meteo" />
            : <SourceLink href={SRC.epqs} label="USGS" />)}
        </Row>
        {('low_ground' in r) && <Row k={t('prof.low')}>
          {r.low_ground === true ? t('home.lowGround') : r.low_ground === false ? t('home.notLow') : t('prof.unknown')}
          {r.low_ground == null && r.low_ground_note && <span className="block text-caption text-muted">{coded(bk, r as never, 'low_ground_note')}</span>}
          {r.low_ground === true && <SourceLink href={SRC.flat} label="Harris County MAAPnext" />}
        </Row>}
        <Row k={t('prof.reservoir')}>
          {typeof r.reservoir_area === 'string' && r.reservoir_area ? r.reservoir_area : yn(r.reservoir_area == null ? null : !!r.reservoir_area)}
          {!!r.reservoir_area && <SourceLink href={SRC.dams} label="Texas Tribune" />}
        </Row>
        <Row k={t('prof.jurisdiction')}>{bk(r.jurisdiction_code, r.jurisdiction_params, r.jurisdiction ?? '—')}</Row>
      </dl>
      {loc && <NeighborhoodChip lat={loc.lat} lon={loc.lon} />}
      {facts.length > 0 && (
        <section>
          <h4 className="text-h3 text-ink">{t('prof.misses')}</h4>
          <ul className="mt-2 space-y-3">
            {facts.map((f, i) => <li key={i} className="text-body-sm text-ink">{bk(f.code, f.params, f.text)}<SourceLink href={f.source} /></li>)}
          </ul>
        </section>
      )}
    </div>
  )
}

/** Storms on record with the peak at the nearest stream gauge. */
export function FloodHistoryList({ h }: { h: FloodHistory }) {
  const { t, lang } = useApp()
  const events = (Array.isArray(h.events) ? h.events : []).filter((e) => e && e.id)
  if (!events.length && !h.zip?.peak_year) return <p className="text-body-sm text-muted">{t('det.historyNone')}</p>
  return (
    <div className="space-y-3">
      <ul className="divide-y divide-line">
        {events.map((e) => {
          const g = e.nearest_gauge
          const date = Date.parse(e.start)
          return (
            <li key={e.id} className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1 py-3 first:pt-0">
              <span className="min-w-0">
                <span className="block text-body-sm font-semibold text-ink">{e.name}</span>
                <span className="block text-caption text-muted">
                  {!isNaN(date) ? new Date(date).toLocaleDateString(lang, { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }) : e.start}
                  {g ? ` · ${g.peak_ft != null ? g.peak_ft + ' ft · ' : ''}${g.name}, ${typeof g.distance_mi === 'number' ? g.distance_mi.toFixed(1) + ' mi' : ''}` : ` · ${t('c6.hist.noGauge')}`}
                  {g && <SourceLink href={NOAA_GAUGE(g.id)} />}
                </span>
              </span>
              {g && <StatusBadge status={g.peak_category} />}
            </li>
          )
        })}
      </ul>
      {h.zip && h.zip.peak_year != null && (
        <p className="text-body-sm text-ink">{fill(t, 'c6.hist.zip', { zip: h.zip.zip ?? '', year: h.zip.peak_year, n: h.zip.peak_year_claims != null ? h.zip.peak_year_claims.toLocaleString(lang) : '—' })}
          <SourceLink href="https://www.fema.gov/openfema-data-page/nfip-redacted-claims-v3" label="OpenFEMA NFIP" /></p>
      )}
      <p className="text-caption text-muted">{t('c6.hist.note')}</p>
      <a href="#replay" className="inline-flex min-h-11 items-center text-body-sm font-semibold text-brand underline underline-offset-2">{t('det.replay')}</a>
    </div>
  )
}
