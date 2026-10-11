import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { CircleMarker, Polyline, Popup, Tooltip } from 'react-leaflet'
import { ArrowUpDown, Car, LocateFixed, Megaphone, Square, TriangleAlert, Volume2, X } from 'lucide-react'
import { ApiError, api, errText, type DemoRoute, type LatLon, type RouteCheck, type WatchPlace } from '../api'
import { useApp } from '../ctx'
import { Map } from '../components/maps'
import { useAreaAlerts, useWarningsOn, WarningsBar, WarningsMapLayer } from '../components/WarningsLayer'
import { speak, stopSpeaking } from '../components/speak'
import ParkCard from '../components/parking/ParkCard'
import PosterSheet from '../components/poster/PosterSheet'
import ReportSheet from '../components/ReportSheet'
import VoteButtons from '../components/VoteButtons'
import { useAsync, Warnings } from '../components/ui'
import { Button, Card, DemoPanel, Disclosure, ErrorBox, Freshness, IconButton, PageHeader, RiskBadge, Skeleton, SourceLink, inputCls } from '../components/ds'
import { cssVar, verdictLabelKey, verdictLevel } from '../lib/levels'
import { parseHash } from '../components/shell/nav'
import { hazardReason, hazName, routeMessage, useBk } from '../lib/bk'
import { clearDemoGo, peekDemoGo } from '../lib/demoGo'
import OfflineNotice from '../components/OfflineNotice'
import { placeName, store, streetOf, usePlace, useDemoMode, useSimStorm } from '../state/place'
import { AirportChip } from '../components/p35/P35'
import SimToggle from '../components/SimToggle'

/** One end of the route: text, optional known coordinates, and whether it is My place. */
interface Pt { text: string; ll?: LatLon; mine?: boolean }
const EMPTY: Pt = { text: '' }
const LAST = 'floodready.lastRoute'
const TO_KEY = 'floodready.driveTo'
interface Saved { res: RouteCheck; from: string; to: string; at?: number }

export default function Drive() {
  const { t, lang } = useApp()
  const bk = useBk()
  const rsn = (p: { reason_codes?: ({ code: string; params?: Record<string, unknown> } | null)[] }, i: number, r: string) => bk(p.reason_codes?.[i]?.code, p.reason_codes?.[i]?.params, r)
  const { place } = usePlace()
  const { demo, setDemo } = useDemoMode()
  const crossings = useAsync(() => api.crossings(), [])
  const samples = useAsync(() => (demo ? api.routeDemo() : Promise.resolve([] as DemoRoute[])), [demo])
  const mine = (): Pt => (place ? { text: place.label, ll: place, mine: true } : EMPTY)
  const [from, setFrom] = useState<Pt>(mine)
  const [to, setTo] = useState<Pt>(() => {
    // Alerts can hand over a destination ("Check a route here") through sessionStorage.
    const v = store.get(TO_KEY, true); store.set(TO_KEY, null, true)
    try { const p = JSON.parse(v || 'null'); if (p && Number.isFinite(p.lat) && Number.isFinite(p.lon)) return { text: p.label, ll: { lat: p.lat, lon: p.lon } } } catch { /* ignore */ }
    const m = /^to=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/.exec(parseHash().sub ?? '')
    if (m && Math.abs(+m[1]) <= 90 && Math.abs(+m[2]) <= 180) return { text: `${m[1]}, ${m[2]}`, ll: { lat: +m[1], lon: +m[2] } }
    return EMPTY
  })
  // Judge step 2: preselect the Allen Parkway sample route with the storm simulation on (demo mode only).
  const [demoGo] = useState(() => peekDemoGo(2))
  const { sim, setSim } = useSimStorm()
  const demoApplied = useRef(false)
  const [sample, setSample] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [off, setOff] = useState(false)
  const [res, setRes] = useState<RouteCheck | null>(null)
  const [simulated, setSimulated] = useState(false)
  const [cached, setCached] = useState<Saved | null>(() => store.json<Saved | null>(LAST, null))
  const [speaking, setSpeaking] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [poster, setPoster] = useState<{ name: string; lat: number; lon: number } | null>(null)
  const head = useRef<HTMLHeadingElement>(null)

  // My place follows the saved place until the user edits From.
  useEffect(() => { setFrom((f) => (f.mine || !f.text) && place ? { text: place.label, ll: place, mine: true } : f) }, [place])
  useEffect(() => { if (demoGo && !demo) setDemo(true) }, [demoGo, demo, setDemo])
  useEffect(() => {
    if (!demoGo || demoApplied.current || !Array.isArray(samples.data)) return
    demoApplied.current = true
    const r = samples.data.find((x) => /allen/i.test(x?.label ?? '') && x.origin && x.destination)
    clearDemoGo()
    if (!r) return
    setFrom({ text: t('p6.drive.start').replace('{label}', r.label), ll: r.origin }); setTo({ text: t('p6.drive.end').replace('{label}', r.label), ll: r.destination }); setSample(true); setSim(true)
  }, [demoGo, samples.data, t])
  // Real users never get a simulated route, even if a flag was left over.
  const simOn = sim
  const { place: areaPlace } = usePlace()
  const area = useAreaAlerts(areaPlace ?? { lat: 29.76, lon: -95.37 })
  const [warnOn, setWarnOn] = useWarningsOn(area)

  const watched = useMemo(() => store.json<WatchPlace[]>('watchPlaces', []).filter((w) => Number.isFinite(w.lat) && Number.isFinite(w.lon)).slice(0, 3), [])
  const pts = useMemo(() => (Array.isArray(crossings.data?.features) ? crossings.data!.features : []).flatMap((f) => {
    const c = f?.geometry?.coordinates as unknown
    return f?.properties && f.geometry.type === 'Point' && Array.isArray(c) && Number.isFinite(c[0]) && Number.isFinite(c[1]) ? [{ p: f.properties, lat: c[1] as number, lon: c[0] as number }] : []
  }), [crossings.data])

  const resolve = async (p: Pt): Promise<LatLon> => {
    if (p.ll) return { lat: p.ll.lat, lon: p.ll.lon }
    try { const g = await api.geocode(p.text); return { lat: g.lat, lon: g.lon } }
    catch { throw new Error(t('p3.drive.notFound').replace('{text}', p.text)) }
  }
  useEffect(() => {
    if (busy || !res) return
    const id = setTimeout(() => { head.current?.focus({ preventScroll: true }); head.current?.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }) }, 30)
    return () => clearTimeout(id)
  }, [res, busy])
  const check = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!from.text.trim() || !to.text.trim()) { setErr(t('p3.drive.needBoth')); return }
    setBusy(true); setErr(null); setOff(false); setRes(null); stopSpeaking(); setSpeaking(false)
    try {
      const [o, d] = await Promise.all([resolve(from), resolve(to)])
      const r = await api.routeCheck(o, d, simOn)
      setRes(r); setSimulated(simOn)
      if (!simOn) { const s = { res: r, from: from.text, to: to.text, at: Date.now() }; setCached(s); store.set(LAST, JSON.stringify(s)) }
    } catch (e2) { if (e2 instanceof ApiError && e2.status === 0) setOff(true); else setErr(errText(e2, t('p3.drive.offline'))) } finally { setBusy(false) }
  }
  const useMyLocation = () => {
    setErr(null)
    try {
      navigator.geolocation.getCurrentPosition(
        (p) => setFrom({ text: t('p3.drive.curLoc'), ll: { lat: p.coords.latitude, lon: p.coords.longitude } }),
        () => setErr(t('p3.drive.locFail')), { enableHighAccuracy: true, timeout: 10000 })
    } catch { setErr(t('p3.drive.locFail')) }
  }

  // After a failed check (offline) the last good result stays visible, labelled as such.
  const shown = res ?? (err && cached ? cached.res : null)
  const showingCache = !res && !!shown
  const failed = !!shown && !shown.route
  const level = failed ? 'unknown' : verdictLevel(shown?.verdict)
  const hazards = shown?.hazards ?? []
  const line = shown?.route?.coordinates?.map(([lon, lat]) => [lat, lon] as [number, number])
  const bounds = line && line.length > 1 ? line : undefined
  const sampleTag = sample && !simulated

  const toggleSpeak = () => {
    if (speaking) { stopSpeaking(); setSpeaking(false); return }
    if (!shown) return
    setSpeaking(true)
    speak(`${t(failed ? 'verdict.unknown' : verdictLabelKey(shown.verdict))}. ${failed ? t('p3.drive.failed') : routeMessage(bk, t, shown)}`, lang, () => setSpeaking(false))
  }

  const cHigh = cssVar('--danger'), cMed = cssVar('--watch'), cRoute = cssVar('--water'), cRing = '#ffffff'

  return (
    <div className="space-y-4">
      <PageHeader title={t('p3.drive.title')} subtitle={t('p3.drive.sub')} forPlace />

      <Card tone="watch" className="flex items-start gap-3">
        <Car aria-hidden size={28} className="mt-0.5 shrink-0 text-watch" />
        <div>
          <p className="text-h3 text-ink">{t('p3.drive.banner1')}</p>
          <p className="text-body-sm text-ink">{t('p3.drive.banner2')}</p>
        </div>
      </Card>

      <DemoPanel title={t('p3.drive.demoSamples')}>
        <div className="flex flex-wrap gap-2">
          {(Array.isArray(samples.data) ? samples.data : []).filter((r) => r?.origin && r?.destination).map((r) => (
            <button key={r.label} type="button" className="min-h-11 rounded-full border border-watch bg-surface px-3 text-body-sm font-medium text-ink"
              onClick={() => { setFrom({ text: t('p6.drive.start').replace('{label}', r.label), ll: r.origin }); setTo({ text: t('p6.drive.end').replace('{label}', r.label), ll: r.destination }); setSample(true); setRes(null); setErr(null) }}>
              {r.label}
            </button>
          ))}
        </div>
      </DemoPanel>
      <SimToggle />
      <AirportChip />

      <Card>
        <form onSubmit={check} className="space-y-3">
          <PointField label={t('p3.drive.from')} pt={from} placeholder={t('p3.drive.fromHint')}
            onChange={(p) => { setFrom(p); setSample(false) }}
            extra={<IconButton icon={LocateFixed} label={t('p3.drive.useLoc')} variant="secondary" onClick={useMyLocation} />} />
          <div className="flex justify-center">
            <IconButton icon={ArrowUpDown} label={t('p3.drive.swap')} variant="secondary" onClick={() => { setFrom(to); setTo(from); setSample(false) }} />
          </div>
          <PointField label={t('p3.drive.to')} pt={to} placeholder={t('p3.drive.toHint')} onChange={(p) => { setTo(p); setSample(false) }} />
          {watched.length > 0 && (
            <div className="flex flex-wrap items-center gap-2" role="group" aria-label={t('p3.drive.watched')}>
              {watched.map((w) => (
                <button key={w.id} type="button" onClick={() => setTo({ text: w.label, ll: { lat: w.lat, lon: w.lon } })}
                  className="min-h-11 rounded-full border border-ui bg-surface px-3 text-body-sm font-medium text-ink hover:bg-surface-2">{w.label}</button>
              ))}
            </div>
          )}
          <Button type="submit" size="lg" full loading={busy}>{t('p3.drive.check')}</Button>
        </form>
      </Card>

      {off && <OfflineNotice at={cached?.at ?? null} />}
      {err && <ErrorBox error={err} onRetry={() => document.querySelector<HTMLFormElement>('form')?.requestSubmit()} />}
      {err && cached && !res && <p className="text-caption text-muted">{t('p3.drive.offline')}</p>}

      <div aria-live="polite" aria-busy={busy}>
        {busy && (
          <Card aria-busy><Skeleton w="140px" h={32} radius={999} /><div className="mt-3 space-y-2"><Skeleton w="100%" h={18} /><Skeleton w="70%" h={18} /></div></Card>
        )}
        {!busy && shown && (
          <Card tone={level} className="scroll-mt-16">
            {showingCache && <p className="mb-2 text-caption font-semibold text-muted">{t('p3.drive.lastRoute')}: {cached?.from} → {cached?.to}</p>}
            <h2 ref={head} tabIndex={-1} className="outline-none">
              <RiskBadge level={level} size="lg" label={t(failed ? 'verdict.unknown' : verdictLabelKey(shown.verdict))} suffix={simulated && !showingCache ? t('demo.simulated') : undefined} />
            </h2>
            {!failed && !(simulated && !showingCache) && <div className="mt-2"><Freshness meta={shown.meta} /></div>}
            {simulated && !showingCache && <p className="mt-2 text-caption font-semibold text-watch">{t('p3.drive.simNote')}</p>}
            {sampleTag && <p className="mt-2 text-caption font-semibold text-watch">{t('p3.drive.sample')}</p>}
            <p className="mt-3 text-h3 font-normal text-ink">{failed ? t('p3.drive.failed') : routeMessage(bk, t, shown)}</p>
            <div className="mt-2"><Warnings items={shown.warnings} codes={shown.warning_codes} /></div>
            <h3 className="mt-4 text-h3 text-ink">{t('p3.drive.hazards')}</h3>
            {hazards.length === 0 ? <p className="mt-1 text-body-sm text-muted">{t('p3.drive.noHazards')}</p> : (
              <ul className="mt-2 divide-y divide-line">
                {hazards.map((h, i) => (
                  <li key={i} className="flex items-start gap-3 py-3">
                    {h.kind === 'report' ? <Megaphone aria-hidden size={20} className="mt-0.5 shrink-0 text-watch" /> : <TriangleAlert aria-hidden size={20} className="mt-0.5 shrink-0 text-danger" />}
                    <div className="min-w-0">
                      <p className="text-base font-semibold text-ink">{hazName(bk, h)}
                        {h.kind === 'report' && <span className="ms-2 rounded-sm border border-dashed border-ui px-1.5 text-caption font-medium text-muted">{t('p3.drive.reportTag')}</span>}
                      </p>
                      <p className="text-body-sm text-ink">{hazardReason(bk, h)}{h.kind === 'report' && <span className="text-muted"> {t('p3.drive.unverified')}</span>}</p>
                      {h.kind === 'report' && h.report_id && <VoteButtons id={h.report_id} />}
                      {h.kind !== 'report' && Number.isFinite(h.lat) && Number.isFinite(h.lon) && <button type="button" className="text-body-sm text-brand underline" onClick={() => setPoster({ name: h.name, lat: h.lat, lon: h.lon })}>{t('poster.act')}</button>}
                      {h.kind !== 'report' && (crossings.data?.features ?? []).find((f) => f?.properties?.id === h.crossing_id)?.properties?.sources?.slice(0, 1).map((s) => <SourceLink key={s} href={s} />)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="secondary" icon={speaking ? Square : Volume2} onClick={toggleSpeak} aria-pressed={speaking}>{speaking ? t('p3.drive.stop') : t('p3.drive.read')}</Button>
              <Button variant="secondary" icon={Megaphone} onClick={() => setReportOpen(true)}>{t('p3.drive.report')}</Button>
            </div>
          </Card>
        )}
      </div>

      <ParkCard />

      {crossings.error && <ErrorBox error={crossings.error} onRetry={crossings.reload} />}
      <WarningsBar data={area} on={warnOn} onChange={setWarnOn} />
      <Map label={t('p3.drive.mapLabel')} bounds={bounds} height="h-80 md:h-[440px]" loading={busy || crossings.loading}
        legend={<>
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="size-3 rounded-full" style={{ background: cHigh }} />{t('p3.drive.legendHigh')}</span>
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="size-3 rounded-full" style={{ background: cMed }} />{t('p3.drive.legendMed')}</span>
          <span className="inline-flex items-center gap-1.5"><TriangleAlert aria-hidden size={14} className="text-danger" />{t('p3.drive.legendHaz')}</span>
        </>}>
        <WarningsMapLayer data={area} on={warnOn} />
        {pts.map(({ p, lat, lon }) => (
          <CircleMarker key={p.id} center={[lat, lon]} radius={6}
            pathOptions={{ color: cRing, weight: 1.5, fillColor: p.risk === 'high' ? cHigh : cMed, fillOpacity: 0.9 }}>
            <Popup>
              <b>{p.name}</b> ({p.risk})
              <ul className="list-disc ps-4">{(p.reasons ?? []).map((r, i) => <li key={i}>{rsn(p, i, r)}</li>)}</ul>
              {(p.sources ?? []).map((s) => <div key={s}><SourceLink href={s} /></div>)}
            </Popup>
          </CircleMarker>
        ))}
        {line && <Polyline positions={line} pathOptions={{ color: cRoute, weight: 5 }} />}
        {hazards.filter((h) => Number.isFinite(h.lat) && Number.isFinite(h.lon)).map((h, i) => (
          <CircleMarker key={i} center={[h.lat, h.lon]} radius={10} pathOptions={{ color: cRing, weight: 2, fillColor: cHigh, fillOpacity: 1 }}>
            <Tooltip permanent direction="top">{hazName(bk, h)}</Tooltip>
          </CircleMarker>
        ))}
      </Map>
      <p className="-mt-2 text-caption text-muted">{t('p3.drive.mapHint')}</p>
      {crossings.data && pts.length === 0 && <p className="text-body-sm text-muted">{t('p3.drive.noCrossings')}</p>}
      {pts.length > 0 && (
        <Disclosure id="crossings" title={t('p3.drive.crossingsList').replace('{n}', String(pts.length))}>
          <ul className="list-disc space-y-1 ps-5 text-body-sm">
            {pts.map(({ p }) => <li key={p.id}><b>{p.name}</b>: {t('p3.drive.crossingRisk').replace('{risk}', t('p3.drive.risk.' + p.risk))}{(p.reasons ?? []).length > 0 && <> ({(p.reasons ?? []).map((r, i) => rsn(p, i, r)).join('; ')})</>}</li>)}
          </ul>
        </Disclosure>
      )}
      {poster && <PosterSheet {...poster} onClose={() => setPoster(null)} />}
      <ReportSheet open={reportOpen} onClose={() => setReportOpen(false)} />
    </div>
  )
}

function PointField({ label, pt, onChange, placeholder, extra }: {
  label: string; pt: Pt; onChange: (p: Pt) => void; placeholder: string; extra?: React.ReactNode
}) {
  const { t } = useApp()
  const { place } = usePlace()
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-body-sm font-medium text-ink">{label}</label>
      <div className="flex gap-2">
        {pt.mine && place ? (
          <div id={id} className={`${inputCls} flex items-center gap-2`}>
            <span className="inline-flex shrink-0 items-center rounded-full bg-brand-tint px-2 text-caption font-semibold text-brand">{placeName(place.nickname, t)}</span>
            <span className="min-w-0 flex-1 truncate text-body-sm">{streetOf(pt.text)}</span>
            <button type="button" aria-label={t('p3.drive.clear')} onClick={() => onChange(EMPTY)} className="inline-flex size-8 shrink-0 items-center justify-center rounded-sm text-muted hover:bg-surface-2"><X aria-hidden size={16} /></button>
          </div>
        ) : (
          <input id={id} className={`${inputCls} min-w-0 flex-1`} value={pt.text} placeholder={placeholder} autoComplete="street-address"
            onChange={(e) => onChange({ text: e.target.value })} />
        )}
        {extra}
      </div>
    </div>
  )
}
