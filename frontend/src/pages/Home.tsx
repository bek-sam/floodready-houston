import { useCallback, useEffect, useMemo, useState } from 'react'
import { BookOpen, ChevronRight, FileText, History, Landmark, MapPinPlus, ShieldCheck, Waves, Home as HomeIcon, type LucideIcon } from 'lucide-react'
import { api, ApiError, type Alerts, type FloodHistory, type LatLon, type Outlook, type Risk, type ZipInsurance } from '../api'
import { HOUSTON, useApp } from '../ctx'
import { placeName, store, usePlace, useSimStorm } from '../state/place'
import { useShell } from '../components/shell/ShellContext'
import { exposure as computeExposure, fill, profilePreview, rightNow, type Src, type SummaryInputs } from '../lib/summary'
import { Button, Card, Disclosure, EmptyState, ErrorBox, LoadingText, SkeletonText, toast } from '../components/ds'
import { SummaryHero } from '../components/home/SummaryHero'
import { TopActions } from '../components/home/TopActions'
import { LiveConditions } from '../components/home/LiveConditions'
import { FloodHistoryList, PlaceProfile } from '../components/home/PlaceProfile'
import EvacSurgeBody, { evacShow, useEvac } from '../components/evac/EvacSurgeCard'
import HwmBody, { hasMarks, useHwm } from '../components/hwm/HwmCard'
import DigestBanner from '../components/digest/DigestBanner'
import RainCard from '../components/rain24/RainCard'
import CoastalChip from '../components/coastal/CoastalChip'
import RentBuy from '../components/RentBuy'
import { clearDemoGo, peekDemoGo } from '../lib/demoGo'
import SimToggle from '../components/SimToggle'

const SAMPLE_ADDRESS = '5300 N Braeswood Blvd, Houston, TX 77096' // the demo address in DEMO-DAY.md
const CACHE_KEY = 'floodready.homeCache.v1'

interface Res<T> extends Src<T> { at: number | null; cached: boolean; loading: boolean }
interface State<T> extends Res<T> { k: string }
const EMPTY: Res<never> = { data: null, failed: false, done: false, at: null, cached: false, loading: true }

type Cache = Record<string, { k: string; at: number; data: unknown }>
const readCache = (name: string, k: string) => { const c = store.json<Cache>(CACHE_KEY, {})[name]; return c && c.k === k ? c : null }
const writeCache = (name: string, k: string, data: unknown) => {
  const c = store.json<Cache>(CACHE_KEY, {})
  c[name] = { k, at: Date.now(), data }
  store.set(CACHE_KEY, JSON.stringify(c))
}

/**
 * Fetch one endpoint for `key` (null = disabled). A new key resets to loading (no stale data from the
 * previous place); a refresh (`nonce`) keeps the current data until the new result lands.
 * When offline, falls back to the last saved result for the same key.
 */
function useSrc<T>(name: string, key: string | null, fn: () => Promise<T>, nonce: number): Res<T> {
  const [s, setS] = useState<State<T>>({ ...EMPTY, k: '' })
  useEffect(() => {
    if (!key) return
    let live = true
    setS((p) => (p.k === key ? { ...p, loading: true } : { ...EMPTY, k: key }))
    fn().then((data) => {
      if (!live) return
      writeCache(name, key, data)
      setS({ k: key, data, failed: false, done: true, at: Date.now(), cached: false, loading: false })
    }).catch((e) => {
      if (!live) return
      const c = e instanceof ApiError && e.status === 0 ? readCache(name, key) : null
      setS(c ? { k: key, data: c.data as T, failed: false, done: true, at: c.at, cached: true, loading: false }
        : { k: key, data: null, failed: true, done: true, at: Date.now(), cached: false, loading: false })
    })
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, nonce])
  if (!key) return { ...EMPTY, loading: false, done: true }
  if (s.k !== key) return EMPTY
  return s
}

function useHomeData(loc: LatLon | null, zip: string | null, tag: string) {
  const [nonce, setNonce] = useState(0)
  const refresh = useCallback(() => setNonce((n) => n + 1), [])
  const { sim } = useSimStorm() // demo mode only; false for real users
  const k = loc ? `${tag}${sim ? '-sim' : ''}:${loc.lat.toFixed(5)},${loc.lon.toFixed(5)}` : null
  const risk = useSrc<Risk>('risk', k, () => api.risk(loc!, sim), nonce)
  const alerts = useSrc<Alerts>('alerts', k, () => api.alerts(loc!, sim), nonce)
  const outlook = useSrc<Outlook>('outlook', k, () => api.outlook(loc!, sim), nonce)
  const hist = useSrc<FloodHistory>('hist', tag === 'place' ? k && k + ':' + (zip ?? '') : null, () => api.floodHistory(loc!, zip ?? undefined), nonce)
  const zipIns = useSrc<ZipInsurance>('zip', tag === 'place' && zip ? 'zip:' + zip : null, () => api.zipInsurance(zip!), nonce)
  const all = [risk, alerts, outlook, hist, ...(zip ? [zipIns] : [])]
  const doneAts = all.filter((s) => s.done && s.at != null && !s.cached).map((s) => s.at!)
  const cachedAts = all.filter((s) => s.cached && s.at != null).map((s) => s.at!)
  return {
    inputs: { risk, alerts, outlook, hist, zip: zip ? zipIns : null } as SummaryInputs,
    updatedAt: doneAts.length ? Math.max(...doneAts) : cachedAts.length ? Math.max(...cachedAts) : null,
    offlineAt: cachedAts.length ? Math.min(...cachedAts) : null,
    refreshing: all.some((s) => s.loading),
    refresh,
  }
}

function LinkRow({ href, icon: Icon, title, preview }: { href: string; icon: LucideIcon; title: string; preview: string }) {
  return (
    <a href={href} className="flex min-h-14 items-center gap-3 rounded-lg border border-line bg-surface px-4 py-2 shadow-card hover:bg-surface-2/60">
      <Icon aria-hidden size={20} className="shrink-0 text-brand" />
      <span className="min-w-0 flex-1">
        <span className="block text-h3 text-ink">{title}</span>
        <span className="block truncate text-caption text-muted">{preview}</span>
      </span>
      <ChevronRight aria-hidden size={20} className="shrink-0 text-muted rtl:rotate-180" />
    </a>
  )
}

const Busy = () => <div aria-busy="true"><LoadingText /><SkeletonText lines={4} /></div>

function TrustCard() {
  const { t } = useApp()
  return (
    <Card tone="inset" title={<span className="flex items-center gap-2"><ShieldCheck aria-hidden size={18} className="text-brand" />{t('trust.title')}</span>} titleAs="h2">
      <p className="text-body-sm text-ink">{t('trust.body')}</p>
      <a href="#about" className="mt-2 inline-flex min-h-11 items-center gap-1.5 text-body-sm font-semibold text-brand underline underline-offset-2">
        <BookOpen aria-hidden size={16} />{t('trust.link')}
      </a>
    </Card>
  )
}

/** Load the sample (demo) address as My place. */
function useSample() {
  const { t } = useApp()
  const { setPlace } = usePlace()
  const [busy, setBusy] = useState(false)
  const sample = useCallback(async () => {
    setBusy(true)
    try {
      const g = await api.geocode(SAMPLE_ADDRESS)
      setPlace({ lat: g.lat, lon: g.lon, label: g.matched_address || SAMPLE_ADDRESS })
      toast(t('place.saved'))
    } catch { toast({ message: t('empty.sampleFail'), tone: 'error' }) }
    setBusy(false)
  }, [setPlace, t])
  return { busy, sample }
}

/** No place yet: empty hero + Houston right now (§4.6). */
function NoPlace() {
  const { t } = useApp()
  const { openPlaceSheet } = useShell()
  const { busy, sample } = useSample()
  const d = useHomeData(HOUSTON, null, 'houston')
  return (
    <div className="space-y-6 md:space-y-8">
      <section className="rounded-xl border border-line bg-surface shadow-card">
        <EmptyState icon={MapPinPlus} title={<span className="text-h2">{t('empty.title')}</span>} body={t('empty.body')}
          action={<Button size="lg" icon={MapPinPlus} onClick={openPlaceSheet}>{t('empty.cta')}</Button>}
          secondary={<Button variant="ghost" loading={busy} onClick={sample}>{t('empty.sample')}</Button>} />
      </section>
      <SimToggle />
      <LiveConditions title={t('live.houston')} loc={HOUSTON} risk={d.inputs.risk} alerts={d.inputs.alerts} outlook={d.inputs.outlook}
        updatedAt={d.updatedAt} onRetry={d.refresh} wide />
      <TrustCard />
    </div>
  )
}

export default function Home() {
  const { t } = useApp()
  const { place } = usePlace()
  const { sim } = useSimStorm()
  const { setDanger } = useShell()
  const loc = useMemo(() => (place ? { lat: place.lat, lon: place.lon } : null), [place?.lat, place?.lon]) // eslint-disable-line react-hooks/exhaustive-deps
  const d = useHomeData(loc, place?.zip ?? null, 'place')
  const evac = useEvac(loc)
  const inputs = useMemo(() => ({ ...d.inputs, evac }), [d.inputs, evac])
  const now = rightNow(inputs)
  const exp = computeExposure(inputs)
  const name = place ? placeName(place.nickname, t) : ''
  const { sample } = useSample()
  const hwm = useHwm(loc)
  // Judge step 1: make sure the demo place is loaded (the Judge page normally sets it before navigating).
  useEffect(() => { if (peekDemoGo(1)) { clearDemoGo(); if (!place) void sample() } }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Escalate the 911 strip only when Right now = Danger.
  const dangerText = place && now.final && now.level === 'danger' ? (now.reason.key === 'sum.now.event' ? now.dangerEvent! : `${t('gauge.major')}: ${now.dangerEvent}`) : null
  useEffect(() => { setDanger(dangerText) }, [dangerText, setDanger])

  if (!place) return <NoPlace />

  const r = inputs.risk.data
  const h = inputs.hist.data
  const histN = (h?.events ?? []).filter((e) => e?.nearest_gauge).length

  return (
    <div className="space-y-5 md:space-y-8">
      <h1 className="sr-only">{t('nav.home')}</h1>
      <SimToggle />
      {sim && <p className="text-caption font-semibold text-watch" data-testid="simulated-tag">{t('p34.simulated')}</p>}
      <SummaryHero placeLabel={name} inputs={inputs} now={now} exp={exp}
        updatedAt={d.updatedAt} offlineAt={d.offlineAt} refreshing={d.refreshing} onRefresh={d.refresh} />

      {/* Mobile order: actions, conditions, details, trust. Desktop: those stack on the left; conditions sit in the right column. */}
      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-5 md:gap-6 md:grid-cols-12 md:grid-rows-[auto_auto_1fr] md:gap-x-8">
        <div className="md:col-span-7 md:col-start-1 md:row-start-1">
          <TopActions placeLabel={name} now={now.final ? now.level : 'unknown'} exposure={exp.final ? exp.exposure : 'unknown'}
            ready={now.final && exp.final} />
        </div>
        <div className="md:col-span-5 md:col-start-8 md:row-span-3 md:row-start-1">
          <LiveConditions title={t('live.title')} loc={loc} risk={inputs.risk} alerts={inputs.alerts} outlook={inputs.outlook}
            updatedAt={d.updatedAt} onRetry={d.refresh} />
          <CoastalChip />
          <div className="mt-4"><RainCard loc={loc} /></div>
        </div>

        <section aria-labelledby="det-title" className="space-y-3 md:col-span-7 md:col-start-1 md:row-start-2">
          <h2 id="det-title" className="text-h2 text-ink">{t('det.title')}</h2>
          <DigestBanner inputs={inputs} placeKey={`${loc!.lat.toFixed(4)},${loc!.lon.toFixed(4)}`} />
          <Disclosure id="profile" icon={<HomeIcon size={20} />} title={t('det.profile')}
            preview={r ? profilePreview(r, t) : inputs.risk.failed ? t('live.unavail') : t('sum.checking')}>
            {r ? <PlaceProfile r={r} loc={loc} /> : inputs.risk.failed ? <ErrorBox error={t('sum.exp.unknown')} onRetry={d.refresh} /> : <Busy />}
          </Disclosure>
          <Disclosure id="history" icon={<Waves size={20} />} title={t('det.history')}
            preview={h ? (histN ? fill(t, 'det.historyPreview', { n: histN }) : t('det.historyNone')) : inputs.hist.failed ? t('live.unavail') : t('sum.checking')}>
            {h ? <FloodHistoryList h={h} /> : inputs.hist.failed ? <ErrorBox error={t('live.unavail')} onRetry={d.refresh} /> : <Busy />}
          </Disclosure>
          {evacShow(evac) && evac && (
            <Disclosure id="evac" icon={<Waves size={20} />} title={t('p10.det.evac')} preview={t('p10.det.evacPrev')}><EvacSurgeBody d={evac} /></Disclosure>
          )}
          {hasMarks(hwm) && (
            <Disclosure id="hwm" icon={<History size={20} />} title={t('p10.det.hwm')} preview={t('p10.det.hwmPrev')}><HwmBody d={hwm} /></Disclosure>
          )}
          <Disclosure id="rentbuy" icon={<FileText size={20} />} title={t('det.rentbuy')}
            preview={place.zip ? fill(t, 'det.rentbuyPreview', { zip: place.zip }) : t('det.rentbuyPreviewNoZip')}>
            <RentBuy label={place.label} zone={r?.fema_zone} sfha={r?.sfha} lat={place.lat} lon={place.lon} />
          </Disclosure>
          <LinkRow href="#civic" icon={Landmark} title={t('det.civic')} preview={t('det.civicPreview')} />
          <LinkRow href="#replay" icon={History} title={t('det.replay')} preview={t('det.replayPreview')} />
        </section>

        <div className="md:col-span-7 md:col-start-1 md:row-start-3"><TrustCard /></div>
      </div>
    </div>
  )
}
