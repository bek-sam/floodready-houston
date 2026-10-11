import { useMemo, useState } from 'react'
import type { LatLngBoundsExpression } from 'leaflet'
import { CircleMarker, Tooltip } from 'react-leaflet'
import { BellRing, CloudRain, Map as MapIcon, Waves } from 'lucide-react'
import type { Alert, Alerts, Gauge, LatLon, Outlook, Risk } from '../../api'
import { useApp } from '../../ctx'
import { cssVar, gaugeLabelKey, gaugeLevel, LEVEL_VAR, maxLevel, type Level } from '../../lib/levels'
import { alertLevel, fill, isFloodAlert, milesBetween, SRC, timeOf, type Src } from '../../lib/summary'
import { Map } from '../maps'
import Sparkline from '../Sparkline'
import { Button, Card, Disclosure, ErrorBox, Freshness, GaugeChips, LoadingText, RiskBadge, Sheet, Skeleton, SourceLink, StatTile, StatusBadge } from '../ds'

function AlertRow({ a, onRead }: { a: Alert; onRead: (a: Alert) => void }) {
  const { t, lang } = useApp()
  const lvl = alertLevel(a.event)
  const exp = a.expires ? Date.parse(a.expires) : NaN
  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <RiskBadge level={lvl} label={t('level.' + lvl)} size="sm" />
      <p className="mt-1 text-base font-semibold text-ink">{a.event}</p>
      {a.headline && <p className="text-body-sm text-ink">{a.headline}</p>}
      <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
        {!isNaN(exp) ? <span className="text-caption text-muted">{fill(t, 'live.expires', { time: timeOf(exp, lang) })}</span> : <span />}
        <Button variant="ghost" size="sm" onClick={() => onRead(a)} aria-label={fill(t, 'live.readAria', { event: a.event })}>{t('live.read')}</Button>
      </div>
    </li>
  )
}

function GaugeRow({ g, from }: { g: Gauge; from: LatLon | null }) {
  const { t } = useApp()
  const dist = from && Number.isFinite(g.lat) && Number.isFinite(g.lon) ? milesBetween(from, g).toFixed(1) : null
  const stage = g.stage_ft != null ? String(g.stage_ft) : '—'
  return (
    <li className="grid min-h-16 grid-cols-[1fr_96px] items-center gap-x-3 gap-y-1 py-2 sm:grid-cols-[1fr_auto_96px]">
      <span className="min-w-0">
        <span className="block text-body-sm font-medium text-ink">{g.name}</span>
        <span className="block text-caption text-muted tabular-nums">{dist ? fill(t, 'live.gaugeMeta', { stage, dist }) : `${stage} ft`}</span>
        <span className="mt-1 flex flex-wrap items-center gap-1 sm:hidden"><StatusBadge status={g.status} /><GaugeChips g={g} /></span>
        <span className="mt-1 hidden sm:block"><GaugeChips g={g} /></span>
      </span>
      <span className="hidden sm:block"><StatusBadge status={g.status} /></span>
      <Sparkline id={g.id} width={96} height={32} />
    </li>
  )
}

/** Live conditions: alerts tile, rain outlook tile, nearby gauges (§4.5). */
export function LiveConditions({ title, loc, risk, alerts, outlook, updatedAt, onRetry, wide = false }: {
  title: string; loc: LatLon | null; risk: Src<Risk>; alerts: Src<Alerts>; outlook: Src<Outlook>
  updatedAt: number | null; onRetry: () => void; wide?: boolean
}) {
  const { t, lang } = useApp()
  const [read, setRead] = useState<Alert | null>(null)
  const [map, setMap] = useState(false)
  const all = (alerts.data?.alerts ?? []).filter((a) => a && typeof a.event === 'string')
  const flood = all.filter((a) => isFloodAlert(a.event))
  const other = all.filter((a) => !isFloodAlert(a.event))
  const gauges = (risk.data?.nearest_gauges ?? []).filter((g) => g && g.id)
  const day1 = outlook.data?.day1 ?? null
  const bounds = useMemo<LatLngBoundsExpression | undefined>(() => {
    if (!loc) return undefined
    const pts = [loc, ...gauges].filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lon))
    const lats = pts.map((p) => p.lat), lons = pts.map((p) => p.lon)
    return [[Math.min(...lats) - 0.01, Math.min(...lons) - 0.01], [Math.max(...lats) + 0.01, Math.max(...lons) + 0.01]]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loc?.lat, loc?.lon, risk.data])
  const cat = day1?.category
  const outLevel: Level | undefined = cat === 'Moderate' || cat === 'High' ? 'watch' : cat === 'None' ? 'normal' : undefined
  const alertTop: Level = flood.length ? maxLevel(...flood.map((a) => alertLevel(a.event))) : 'normal'
  const sk = <Skeleton w={110} h={28} />

  return (
    <section aria-labelledby="live-title">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <h2 id="live-title" className="text-h2 text-ink">{title}</h2>
        {updatedAt != null && <span className="text-caption text-muted">{fill(t, 'sum.updated', { time: timeOf(updatedAt, lang) })}</span>}
      </div>
      {(alerts.data?.meta || risk.data?.meta) && (
        <div className="mt-1 flex flex-wrap gap-2"><Freshness meta={alerts.data?.meta} prefix={t('p9.fresh.for.alerts')} /><Freshness meta={risk.data?.meta} prefix={t('p9.fresh.for.gauges')} /></div>
      )}
      <div className={`mt-3 grid gap-3 ${wide ? 'sm:grid-cols-2' : ''}`}>
        <div aria-busy={!alerts.done || undefined} aria-live="polite">
          {!alerts.done && <LoadingText />}
          <StatTile label={t('live.alerts')} icon={BellRing}
            level={alerts.done && !alerts.failed ? alertTop : undefined}
            value={!alerts.done ? sk : alerts.failed ? '—' : flood.length === 0 ? t('live.none')
              : <span className="block truncate text-[20px]">{fill(t, 'live.alertsCount', { n: flood.length, event: flood[0].event })}</span>}
            sub={alerts.failed ? t('live.unavail') : alerts.done && flood.length === 0 ? t('live.noneSub') : undefined}
            source={alerts.failed ? <Button variant="secondary" size="sm" onClick={onRetry}>{t('retry')}</Button> : <SourceLink href={SRC.nws} />} />
        </div>
        <div aria-busy={!outlook.done || undefined}>
          <StatTile label={t('live.outlook')} icon={CloudRain} level={outlook.done && !outlook.failed ? outLevel : undefined}
            value={!outlook.done ? sk : outlook.failed ? '—' : cat ? t('sum.cat.' + cat) : t('live.outlookNone')}
            sub={outlook.failed ? t('live.unavail') : day1?.label && day1.label !== cat ? day1.label : undefined}
            source={outlook.failed ? <Button variant="secondary" size="sm" onClick={onRetry}>{t('retry')}</Button>
              : outlook.data?.source ? <SourceLink href={outlook.data.source} label="NOAA WPC" /> : undefined} />
        </div>
      </div>

      {flood.length > 0 && (
        <Card className="mt-3"><ul className="divide-y divide-line">{flood.map((a, i) => <AlertRow key={i} a={a} onRead={setRead} />)}</ul></Card>
      )}
      {other.length > 0 && (
        <Disclosure className="mt-3" title={fill(t, 'live.otherAlerts', { n: other.length })}>
          <ul className="divide-y divide-line">{other.map((a, i) => <AlertRow key={i} a={a} onRead={setRead} />)}</ul>
        </Disclosure>
      )}

      <Card className="mt-3" title={<span className="flex items-center gap-2"><Waves aria-hidden size={18} className="text-water" />{t('live.gauges')}</span>}
        action={<span className="inline-flex min-h-11 items-center"><SourceLink href={SRC.noaaGauges} label="NOAA" /></span>} aria-busy={!risk.done || undefined}>
        {!risk.done ? (
          <div><LoadingText />{[0, 1, 2].map((i) => (
            <div key={i} className="grid min-h-16 grid-cols-[1fr_96px] items-center gap-3 py-2"><span className="flex flex-col gap-2"><Skeleton w="70%" h={16} /><Skeleton w="40%" h={12} /></span><Skeleton w={96} h={32} /></div>
          ))}</div>
        ) : risk.failed ? (
          <ErrorBox error={t('live.unavail')} onRetry={onRetry} />
        ) : gauges.length === 0 ? (
          <p className="text-body-sm text-muted">{t('live.noGauges')}</p>
        ) : (
          <>
            <ul className="divide-y divide-line">{gauges.map((g) => <GaugeRow key={g.id} g={g} from={loc} />)}</ul>
            <p className="mt-2 text-caption text-muted">{t('live.streamNote')}</p>
            <Button variant="ghost" size="sm" icon={MapIcon} className="-ms-3 mt-1" aria-expanded={map} onClick={() => setMap(!map)}>
              {map ? t('live.hideMap') : t('live.showMap')}
            </Button>
            {map && loc && (
              <div className="mt-2">
                <Map label={t('live.mapLabel')} height="h-60" center={[loc.lat, loc.lon]}
                  bounds={bounds}>
                  <CircleMarker center={[loc.lat, loc.lon]} radius={9} pathOptions={{ color: '#fff', weight: 3, fillColor: cssVar('--brand', '#0B5CAD'), fillOpacity: 1 }}>
                    <Tooltip>{t('live.you')}</Tooltip>
                  </CircleMarker>
                  {gauges.filter((g) => Number.isFinite(g.lat) && Number.isFinite(g.lon)).map((g) => (
                    <CircleMarker key={g.id} center={[g.lat, g.lon]} radius={8}
                      pathOptions={{ color: '#fff', weight: 2, fillColor: cssVar(LEVEL_VAR[gaugeLevel(g.status)]), fillOpacity: 1 }}>
                      <Tooltip>{g.name}: {t(gaugeLabelKey(g.status))}</Tooltip>
                    </CircleMarker>
                  ))}
                </Map>
              </div>
            )}
          </>
        )}
      </Card>

      <Sheet open={!!read} onClose={() => setRead(null)} title={read?.event ?? ''}>
        {read && (
          <div className="space-y-3 text-body-sm text-ink">
            {read.headline && <p className="font-semibold">{read.headline}</p>}
            <p className="whitespace-pre-line">{read.description}</p>
            <p className="text-caption text-muted">{t('source')}:<SourceLink href={SRC.nws} /></p>
          </div>
        )}
      </Sheet>
    </section>
  )
}
