import { useEffect, useState } from 'react'
import { CloudRain } from 'lucide-react'
import type { LatLon } from '../../api'
import { useApp } from '../../ctx'
import { fill, timeOf } from '../../lib/summary'
import { ButtonLink, Card, SkeletonText, SourceLink } from '../ds'
import { parseRain24, type Rain24 } from './parse'

type S = { k: string; state: 'loading' | 'ok' | 'unavail'; data: Rain24 | null }

/** Rain next 24 h at this place: four 6 h NWS QPF bars + hourly chance-of-rain sparkline. Never shows 0 when the forecast failed. */
export default function RainCard({ loc }: { loc: LatLon | null }) {
  const { t, lang } = useApp()
  const k = loc ? `${loc.lat.toFixed(4)},${loc.lon.toFixed(4)}` : ''
  const [s, setS] = useState<S>({ k: '', state: 'loading', data: null })
  useEffect(() => {
    if (!loc) return
    const c = new AbortController()
    fetch(`/api/rain24?lat=${loc.lat}&lon=${loc.lon}`, { signal: c.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((j) => { const d = parseRain24(j); setS({ k, state: d ? 'ok' : 'unavail', data: d }) })
      .catch((e) => { if (e?.name !== 'AbortError') setS({ k, state: 'unavail', data: null }) })
    return () => c.abort()
  }, [k]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!loc) return null
  const cur = s.k === k ? s : { k, state: 'loading' as const, data: null }
  const d = cur.data
  const max = d ? Math.max(1, ...d.windows.map((w) => w.inches)) : 1
  const act = d?.action?.show ? d.action : null
  const hr = (m: number) => timeOf(m, lang)
  return (
    <Card title={<span className="flex items-center gap-2"><CloudRain aria-hidden size={18} className="text-brand" />{t('p15.rain.title')}</span>} titleAs="h2" subtitle={t('p15.rain.sub')}>
      {cur.state === 'loading' && <div aria-busy="true"><SkeletonText lines={3} /></div>}
      {cur.state === 'unavail' && <p className="text-body-sm text-muted">{t('p15.rain.unavail')}</p>}
      {d && (
        <div className="space-y-3">
          {d.windows.length > 0 && (
            <ul className="grid grid-cols-4 gap-2">
              {d.windows.map((w) => (
                <li key={w.start} className="text-center" aria-label={`${hr(w.start)}: ${fill(t, 'p15.rain.in', { n: w.inches.toFixed(2) })}`}>
                  <div className="flex h-16 items-end justify-center rounded bg-surface-2">
                    <div className="w-full rounded bg-water" style={{ height: `${Math.max(4, (w.inches / max) * 100)}%` }} />
                  </div>
                  <p className="mt-1 text-caption font-semibold text-ink">{fill(t, 'p15.rain.in', { n: w.inches.toFixed(2) })}</p>
                  <p className="text-caption text-muted">{hr(w.start)}</p>
                </li>
              ))}
            </ul>
          )}
          {d.pop.length > 1 && (
            <div>
              <p className="text-caption text-muted">{t('p15.rain.pop')}</p>
              <svg viewBox="0 0 240 40" role="img" aria-label={t('p15.rain.pop')} className="h-10 w-full">
                <polyline fill="none" stroke="currentColor" strokeWidth="2" className="text-brand"
                  points={d.pop.map((p, i) => `${(i / (d.pop.length - 1)) * 240},${38 - (p.pct / 100) * 36}`).join(' ')} />
              </svg>
            </div>
          )}
          {d.past && (
            <p className="text-body-sm text-ink">
              {fill(t, 'p32.rain.past', { a: d.past.last24.toFixed(1), b: d.past.last72.toFixed(1) })}{' '}
              <a href={d.past.gaugeUrl ?? 'https://www.harriscountyfws.org'} target="_blank" rel="noreferrer" className="underline">{t('p32.rain.gauges')}</a>
            </p>
          )}
          {act ? (
            <div className="rounded-md bg-surface-2 p-3">
              <p className="text-body-sm font-semibold text-ink">{act.text}</p>
              <ButtonLink href="#drive" size="sm" variant="secondary" className="mt-2">{t('p15.rain.drive')}</ButtonLink>
            </div>
          ) : <p className="text-body-sm text-ink">{t('p15.rain.calm')}</p>}
        </div>
      )}
      <div className="mt-2"><SourceLink href={d?.sourceUrl ?? `https://forecast.weather.gov/MapClick.php?lat=${loc.lat}&lon=${loc.lon}`} label={t('p15.rain.link')} /></div>
    </Card>
  )
}
