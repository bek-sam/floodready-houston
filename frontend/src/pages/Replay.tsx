import { lazy, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { CircleMarker, Tooltip } from 'react-leaflet'
import { Check, History, Pause, Play, Volume2 } from 'lucide-react'
import { api, statusFor, type ReplayGauge } from '../api'
import { useApp } from '../ctx'
import { usePlace, placeName } from '../state/place'
import { cssVar } from '../lib/levels'
import { clearDemoGo, peekDemoGo } from '../lib/demoGo'
import { Map } from '../components/maps'
import StageChart from '../components/StageChart'
import WaterTube from '../components/WaterTube'
import { speak, stopSpeaking } from '../components/speak'
import { mapColor, useAsync } from '../components/ui'
import { Button, Card, Disclosure, EmptyState, ErrorBox, Field, PageHeader, Segmented, Select, Skeleton, SkeletonCard, SourceLink, StatusBadge } from '../components/ds'

const Replay3D = lazy(() => import('../components/replay3d/Replay3D'))

function valueAt(g: ReplayGauge, ms: number): number | null {
  const s = g.series
  let lo = 0, hi = s.length - 1, ans = -1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (Date.parse(s[mid].t) <= ms) { ans = mid; lo = mid + 1 } else hi = mid - 1
  }
  return ans < 0 ? null : s[ans].stage_ft
}
const d2 = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => (a.lat - b.lat) ** 2 + ((a.lon - b.lon) * Math.cos(a.lat * Math.PI / 180)) ** 2
/** Bold the digits already in the summary text (no new numbers). */
const boldNums = (s: string): ReactNode[] => s.split(/(\d[\d,.]*)/).map((p, i) => (i % 2 ? <b key={i}>{p}</b> : p))

export default function Replay() {
  const { t, lang } = useApp()
  // Localized storm name/summary when we have one; otherwise the server's English text.
  const evText = (id: string, f: 'name' | 'summary', fallback: string) => { const k = `p6.ev.${id}.${f}`; const v = t(k); return v === k ? fallback : v }
  const { place } = usePlace()
  const events = useAsync(() => api.replayEvents(), [])
  const [eid, setEid] = useState('')
  useEffect(() => {
    if (eid || !Array.isArray(events.data) || !events.data.length) return
    // Judge step 3 selects Harvey; otherwise the first storm.
    const harvey = peekDemoGo(3) ? events.data.find((e) => /harvey/i.test(`${e.id} ${e.name ?? ''}`)) : undefined
    if (peekDemoGo(3)) clearDemoGo()
    setEid((harvey ?? events.data[0]).id)
  }, [events.data, eid])
  const replay = useAsync(() => api.replay(eid), [eid], !!eid)
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState<'1' | '4'>('1')
  const [gid, setGid] = useState('')
  const [view, setView] = useState<'2d' | '3d'>('2d')
  const [no3d, setNo3d] = useState(false)

  const rawGauges = replay.data?.gauges
  const gauges = useMemo<ReplayGauge[]>(() => (Array.isArray(rawGauges) ? rawGauges : [])
    .filter((g) => g && Number.isFinite(g.lat) && Number.isFinite(g.lon))
    .map((g) => ({ ...g, series: Array.isArray(g.series) ? g.series : [], flood_stages: g.flood_stages ?? { action: null, minor: null, moderate: null, major: null } })), [rawGauges])
  const times = useMemo(() => {
    const s = new Set<number>()
    gauges.forEach((g) => g.series.forEach((p) => { const m = Date.parse(p.t); if (!isNaN(m)) s.add(m) }))
    return [...s].sort((a, b) => a - b)
  }, [gauges])
  useEffect(() => { setIdx(0); setPlaying(false); setGid('') }, [eid])

  const timer = useRef<number | null>(null)
  useEffect(() => {
    if (!playing) return
    const step = Math.max(1, Math.round(times.length / 200)) * (speed === '4' ? 4 : 1)
    timer.current = window.setInterval(() => {
      setIdx((i) => { if (i >= times.length - 1) { setPlaying(false); return i } return Math.min(times.length - 1, i + step) })
    }, 80)
    return () => { if (timer.current) clearInterval(timer.current) }
  }, [playing, times.length, speed])

  const [narrate, setNarrate] = useState(false)
  const cur = times[Math.min(idx, times.length - 1)] ?? 0
  const nearest = useMemo(() => {
    if (!place || !gauges.length) return undefined
    return gauges.reduce((b, g) => (d2(place, g) < d2(place, b) ? g : b), gauges[0])
  }, [place, gauges])
  const selected = gauges.find((g) => g.id === gid) ?? nearest ?? gauges.reduce<ReplayGauge | undefined>(
    (best, g) => (!best || g.series.length > best.series.length ? g : best), undefined)
  const curVal = selected ? valueAt(selected, cur) : null
  const curStatus = selected ? statusFor(curVal, selected.flood_stages) : 'unknown'
  // Narrate: speak when the selected gauge crosses UP into a higher flood stage during playback.
  const prevStatus = useRef<string>('')
  useEffect(() => {
    const order = ['unknown', 'normal', 'action', 'minor', 'moderate', 'major']
    const prev = prevStatus.current
    prevStatus.current = curStatus
    if (!narrate || !playing || !selected || !prev) return
    if (order.indexOf(curStatus) > Math.max(order.indexOf(prev), 1) && curVal != null) {
      speak(t('c3.cross').replace('{name}', selected.name).replace('{level}', curStatus).replace('{ft}', curVal.toFixed(1)), lang)
    }
  }, [curStatus]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { prevStatus.current = '' }, [gid, eid])
  useEffect(() => () => stopSpeaking(), [])
  const bounds = gauges.length ? (gauges.map((g) => [g.lat, g.lon]) as [number, number][]) : undefined
  const evList = Array.isArray(events.data) ? events.data : []
  const ev = replay.data?.event ?? evList.find((e) => e.id === eid)
  const fmtRange = (e: { start: string; end: string }) => {
    const f = (x: string) => { const m = Date.parse(x); return isNaN(m) ? '' : new Date(m).toLocaleDateString(lang, { month: 'short', day: 'numeric', year: 'numeric' }) }
    const a = f(e.start), b = f(e.end)
    return a && b && a !== b ? `${a} – ${b}` : a || b
  }
  const placeLabel = place ? placeName(place.nickname, t) : t('p5.replay.yours')

  return (
    <div className="space-y-4">
      <PageHeader title={t('replay.title')} subtitle={t('p5.replay.sub')} forPlace />

      {events.loading && <div className="grid grid-cols-2 gap-3 md:grid-cols-4" aria-busy="true">{[0, 1, 2, 3].map((i) => <Skeleton key={i} h={88} radius={16} />)}</div>}
      {events.error && <ErrorBox error={events.error} onRetry={events.reload} />}
      {evList.length > 0 && (
        <div role="radiogroup" aria-label={t('p5.replay.pick')}
          className="-mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-1 md:mx-0 md:grid md:grid-cols-4 md:overflow-visible md:px-0">
          {evList.map((e) => {
            const sel = e.id === eid
            return (
              <button key={e.id} type="button" role="radio" aria-checked={sel} onClick={() => setEid(e.id)}
                className={`relative min-h-22 w-40 shrink-0 snap-start rounded-lg bg-surface p-3 text-start shadow-card md:w-auto ${sel ? 'border-2 border-brand' : 'border border-line hover:bg-surface-2/60'}`}>
                <span className="block pe-6 text-h3 text-ink">{evText(e.id, 'name', e.name)}</span>
                <span className="mt-1 block text-caption text-muted">{fmtRange(e)}</span>
                {sel && <Check aria-hidden size={18} className="absolute end-2 top-2 text-brand" />}
              </button>
            )
          })}
        </div>
      )}
      {ev && (
        <Card tone="inset">
          <p className="text-body-sm text-ink">{boldNums(evText(ev.id, 'summary', ev.summary))}{ev.source && <SourceLink href={ev.source} />}</p>
        </Card>
      )}
      {replay.loading && <SkeletonCard lines={5} />}
      {replay.error && <ErrorBox error={replay.error} onRetry={replay.reload} />}

      {replay.data && times.length > 0 && (
        <>
          <div className="sticky top-14 z-10 max-md:-mx-4 md:static">
            <Card padding="md" className="max-md:rounded-none">
              <div className="flex items-center gap-3">
                <Button size="lg" icon={playing ? Pause : Play} aria-pressed={playing} className="w-32"
                  onClick={() => { if (idx >= times.length - 1) setIdx(0); setPlaying(!playing) }}>
                  {playing ? t('replay.pause') : t('replay.play')}
                </Button>
                <div className="min-w-0 flex-1">
                  <label htmlFor="tl" className="block text-caption text-muted">{t('replay.time')}: {new Date(cur).toLocaleString(lang)}</label>
                  <input id="tl" type="range" min={0} max={times.length - 1} value={Math.min(idx, times.length - 1)}
                    onChange={(e) => { setPlaying(false); setIdx(+e.target.value) }} className="h-11 w-full accent-[var(--brand)]"
                    aria-valuetext={`${new Date(cur).toLocaleString(lang)}${selected && curVal != null ? `, ${selected.name} ${curVal.toFixed(1)} ft` : ''}`} />
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <Button variant={narrate ? 'primary' : 'secondary'} size="sm" icon={Volume2} aria-pressed={narrate}
                  onClick={() => { if (narrate) stopSpeaking(); setNarrate(!narrate) }}>
                  {narrate ? t('c3.narrateOff') : t('c3.narrate')}
                </Button>
                <Segmented size="sm" label={t('p5.replay.speed')} value={speed} onChange={setSpeed}
                  options={[{ value: '1', label: '1×' }, { value: '4', label: '4×' }]} />
              </div>
            </Card>
          </div>

          <Segmented size="sm" label={t('p7.view')} value={view} onChange={setView}
            options={[{ value: '2d', label: t('p7.view2d') }, { value: '3d', label: t('p7.view3d') }]} />
          {no3d && <p role="alert" className="text-body-sm text-muted">{t('p7.nowebgl')}</p>}
          {view === '3d' ? (
            <Suspense fallback={<Skeleton h={320} radius={16} />}>
              <Replay3D eventId={eid} gauges={gauges} cur={cur} playing={playing} selectedId={selected?.id} onSelect={setGid}
                place={place} onUnsupported={() => { setNo3d(true); setView('2d') }} />
            </Suspense>
          ) : (
          <Map label={t('replay.title')} bounds={bounds} height="h-72 max-h-[50vh] sm:h-[28rem]">
            {gauges.map((g) => {
              const v = valueAt(g, cur)
              const st = statusFor(v, g.flood_stages)
              return (
                <CircleMarker key={g.id} center={[g.lat, g.lon]} radius={g.id === selected?.id ? 11 : 8}
                  eventHandlers={{ click: () => setGid(g.id) }}
                  pathOptions={{ color: g.id === selected?.id ? cssVar('--ink', '#000') : '#fff', weight: g.id === selected?.id ? 3 : 2, fillColor: mapColor(st), fillOpacity: 0.95 }}>
                  <Tooltip>{g.name}: {v != null ? `${v.toFixed(1)} ft` : '—'}</Tooltip>
                </CircleMarker>
              )
            })}
            {place && (
              <CircleMarker center={[place.lat, place.lon]} radius={7} pathOptions={{ color: '#fff', weight: 3, fillColor: cssVar('--brand'), fillOpacity: 1 }}>
                <Tooltip permanent direction="top">{t('p5.replay.yours')}</Tooltip>
              </CircleMarker>
            )}
          </Map>
          )}
          <div className="flex flex-wrap gap-2" role="group" aria-label={t('p5.replay.legend')}>
            {(['normal', 'action', 'minor', 'moderate', 'major'] as const).map((s) => <StatusBadge key={s} status={s} />)}
          </div>

          <Card title={t('p5.replay.gauges')}>
            <ul className="divide-y divide-line text-body-sm">
              {gauges.map((g) => {
                const v = valueAt(g, cur)
                return (
                  <li key={g.id} className="flex min-h-11 items-center justify-between gap-3 py-1.5">
                    <button type="button" className="min-w-0 truncate text-start font-medium text-brand underline underline-offset-2" onClick={() => setGid(g.id)}>{g.name}</button>
                    <span className="flex shrink-0 items-center gap-2"><span className="tabular-nums text-muted">{v != null ? `${v.toFixed(1)} ft` : '—'}</span><StatusBadge status={statusFor(v, g.flood_stages)} /></span>
                  </li>
                )
              })}
            </ul>
          </Card>

          <Card>
            <Field label={t('replay.gauge')}>
              <Select value={selected?.id ?? ''} onChange={(e) => setGid(e.target.value)}>
                {gauges.map((g) => <option key={g.id} value={g.id}>{g.name}{g.id === nearest?.id ? ` (${placeLabel})` : ''}</option>)}
              </Select>
            </Field>
            {selected && (
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-body-sm font-semibold text-ink">{t('c3.tube')}: {selected.name} <StatusBadge status={curStatus} /></p>
                  <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{selected.name}: {curStatus}{curVal != null ? `, ${curVal.toFixed(1)} ft` : ''}</p>
                  <WaterTube stage={curVal} stages={selected.flood_stages} status={curStatus} title={selected.name} />
                </div>
                <StageChart gauge={selected} cursor={cur} />
              </div>
            )}
          </Card>
        </>
      )}
      {replay.data && times.length === 0 && <EmptyState icon={History} title={t('p5.replay.noData')} />}

      <Disclosure title={t('p5.replay.shiftQ')}><ShiftCard /></Disclosure>
    </div>
  )
}

function ShiftCard() {
  const { t } = useApp()
  const [shifted, setShifted] = useState(false)
  const homes = shifted ? '13,000+' : '~3,600'
  return (
    <div>
      <p className="text-overline uppercase text-muted">{t('replay.published')}</p>
      <p className="mt-1 text-body-sm text-ink">{t('replay.clearCreek')}</p>
      <Segmented className="mt-3" label={t('replay.shiftTitle')} value={shifted ? 'y' : 'n'} onChange={(v) => setShifted(v === 'y')}
        options={[{ value: 'n', label: t('replay.asFell') }, { value: 'y', label: t('replay.shifted') }]} />
      <p className={`mt-3 text-display ${shifted ? 'text-warning' : 'text-ink'}`} aria-live="polite">{homes} {t('replay.homes')}</p>
      <p className="text-body-sm text-muted">{shifted ? t('replay.wouldFloodShifted') : t('replay.wouldFlood')}</p>
      <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden>
        <div className={`h-full rounded-full transition-all ${shifted ? 'bg-warning' : 'bg-water'}`} style={{ width: shifted ? '100%' : '28%' }} />
      </div>
      <p className="mt-3 text-body-sm text-ink">{t('replay.shift')}</p>
      <p className="mt-2 flex flex-wrap gap-x-4 text-body-sm">
        <SourceLink href="https://news.rice.edu/news/2026/10-years-after-tax-day-flood-rice-researchers-warn-hidden-risk" label="Rice News article" />
        <SourceLink href="https://rice1.osn.mghpcc.org/crc-ssl/CFAR_MVP/TaxDayFloodsRevisited/index.html" label="Rice dashboard" />
      </p>
    </div>
  )
}
