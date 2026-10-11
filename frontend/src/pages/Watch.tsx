import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { BellRing, Megaphone, MapPinned, MoreHorizontal, Plus, RefreshCw, Route, Volume2 } from 'lucide-react'
import { ApiError, api, errText, type WatchLevel, type WatchPlace, type WatchStatus } from '../api'
import { useApp } from '../ctx'
import { easyT, useEasy } from '../components/easyread/easyRead'
import AlertsSwitch, { usePush } from '../components/AlertsSwitch'
import ReportSheet from '../components/ReportSheet'
import { speak } from '../components/speak'
import { Button, Card, DemoPanel, EmptyState, ErrorBox, Field, Freshness, GaugeChips, IconButton, PageHeader, RiskBadge, Segmented, Sheet, Skeleton, StatusBadge, Switch, inputCls, toast } from '../components/ds'
import { useShell } from '../components/shell/ShellContext'
import { watchLevel } from '../lib/levels'
import { clearDemoGo, peekDemoGo } from '../lib/demoGo'
import { placeName, store, streetOf, usePlace, useDemoMode } from '../state/place'

const KEY = 'watchPlaces'
const MINE = 'floodready.myWatch'
const RANK: Record<WatchLevel, number> = { ok: 0, watch: 1, warning: 2 }
const NAMES = ['Home', 'Family', 'Work', 'School', 'Other'] as const
const near = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => Math.abs(a.lat - b.lat) < 1e-4 && Math.abs(a.lon - b.lon) < 1e-4

const load = (): WatchPlace[] => { const v = store.json<unknown>(KEY, []); return Array.isArray(v) ? v : [] }
const save = (p: WatchPlace[]) => store.set(KEY, JSON.stringify(p))

export default function Watch() {
  const { t, lang } = useApp()
  const [easy] = useEasy(); const te = (k: string) => easyT(t, k, easy)
  const { place } = usePlace()
  const { demo } = useDemoMode()
  const { openPlaceSheet } = useShell()
  // Judge step 5: bring the push demo controls into view.
  useEffect(() => {
    if (!peekDemoGo(5)) return
    clearDemoGo()
    setTimeout(() => document.getElementById('alerts-demo')?.scrollIntoView({ block: 'start' }), 300)
  }, [])
  const [extra, setExtra] = useState<WatchPlace[]>(load)
  const [mineP, setMineP] = useState<WatchPlace | null>(null)
  const [status, setStatus] = useState<WatchStatus[]>([])
  const [loaded, setLoaded] = useState(false)
  const [sim, setSim] = useState(false)
  const [pollErr, setPollErr] = useState<string | null>(null)
  const [checkedAt, setCheckedAt] = useState<Date | null>(null)
  const [announce, setAnnounce] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [reportOpen, setReportOpen] = useState(false)
  const [menu, setMenu] = useState<WatchPlace | null>(null)
  const prev = useRef<Record<string, WatchLevel>>({})
  const langRef = useRef(lang); langRef.current = lang

  // My place is always watched: register it once with the server and remember its id.
  useEffect(() => {
    if (!place) { setMineP(null); return }
    const c = store.json<WatchPlace | null>(MINE, null)
    if (c && near(c, place)) { setMineP(c); return }
    let live = true
    api.watchSave({ label: place.label, lat: place.lat, lon: place.lon, lang })
      .then((p) => { if (!live) return; const m = { id: p.id, label: p.label, lat: p.lat, lon: p.lon, lang }; store.set(MINE, JSON.stringify(m)); setMineP(m) })
      .catch((e) => { if (live) setPollErr(e instanceof ApiError && e.status === 404 ? t('p3.add.unavailable') : errText(e, t('offline'))) })
    return () => { live = false }
  }, [place, lang, t])

  const others = useMemo(() => extra.filter((p) => p.id !== mineP?.id && !(place && near(p, place))), [extra, mineP, place])
  const places = useMemo(() => (mineP ? [mineP, ...others] : others), [mineP, others])
  const ids = places.map((p) => p.id)
  const push = usePush(ids)
  const pushSub = useRef(push.sub); pushSub.current = push.sub

  const ctl = useRef<AbortController | null>(null)
  const poll = useCallback(async () => {
    ctl.current?.abort()
    if (!ids.length) { setStatus([]); setLoaded(true); return }
    const c = new AbortController(); ctl.current = c
    try {
      const r = await api.watchStatus(ids, demo && sim, c.signal)
      if (c.signal.aborted) return
      const got = Array.isArray(r.places) ? r.places : []
      setPollErr(null); setStatus(got); setCheckedAt(new Date()); setLoaded(true)
      for (const s of got) {
        const before = prev.current[s.id]
        if (before !== undefined && RANK[s.level] > RANK[before] && s.level !== 'ok') {
          const title = t(s.level === 'warning' ? 'p3.announce.warn' : 'p3.announce.watch').replace('{name}', s.label)
          try { if (!pushSub.current && 'Notification' in window && Notification.permission === 'granted') new Notification(title, { body: s.message }) } catch { /* ignore */ }
          setAnnounce(`${title}. ${s.message}`)
          toast({ message: title, tone: s.level === 'warning' ? 'error' : 'default' })
          speak(`${title}. ${s.message}`, langRef.current)
        }
        prev.current[s.id] = s.level
      }
    } catch (e) {
      if (c.signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) return
      setPollErr(errText(e, t('offline'))); setLoaded(true)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(','), demo, sim, t])

  useEffect(() => { prev.current = {} }, [sim])
  useEffect(() => {
    poll()
    const id = setInterval(poll, 120000)
    return () => { clearInterval(id); ctl.current?.abort() }
  }, [poll])

  const remove = (p: WatchPlace) => {
    const n = extra.filter((x) => x.id !== p.id); setExtra(n); save(n); delete prev.current[p.id]
    setMenu(null); toast(t('p3.places.removed').replace('{name}', p.label))
  }
  const checkRoute = (p: WatchPlace) => {
    store.set('floodready.driveTo', JSON.stringify({ label: p.label, lat: p.lat, lon: p.lon }), true)
    location.hash = '#drive'
  }
  const nameOf = (p: WatchPlace) => (mineP && p.id === mineP.id && place ? placeName(place.nickname, t) : p.label)

  if (!place && places.length === 0) {
    return (
      <div>
        <PageHeader title={te('p3.alerts.title')} subtitle={te('p3.alerts.sub')} />
        <EmptyState icon={MapPinned} title={t('p3.noPlace.title')} body={t('p3.noPlace.body')} action={<Button onClick={openPlaceSheet}>{t('p3.noPlace.cta')}</Button>} />
      </div>
    )
  }

  const time = checkedAt ? checkedAt.toLocaleTimeString(lang, { hour: 'numeric', minute: '2-digit' }) : null
  return (
    <div className="space-y-4">
      <PageHeader title={te('p3.alerts.title')} subtitle={te('p3.alerts.sub')} forPlace
        action={<div className="flex items-center gap-1">
          {time && <span className="text-caption text-muted">{t('p3.alerts.checked').replace('{time}', time)}</span>}
          <IconButton icon={RefreshCw} label={te('p3.alerts.refresh')} onClick={() => { void poll() }} />
        </div>} />
      <div className="sr-only" role="alert" aria-live="assertive" aria-atomic="true">{announce}</div>

      <AlertsSwitch push={push} />

      <DemoPanel id="alerts-demo" title={t('p3.demo.title')}>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" disabled={!push.sub || push.busy} onClick={async () => { const n = await push.send('test'); if (n != null) toast(t('p3.demo.sent').replace('{n}', String(n))) }}>{t('p3.demo.test')}</Button>
          <Button variant="secondary" disabled={!push.sub || push.busy} onClick={async () => { const n = await push.send('sim'); if (n != null) toast(t('p3.demo.sent').replace('{n}', String(n))) }}>{t('p3.demo.sim')}</Button>
        </div>
        {!push.sub && <p className="mt-2 text-caption text-muted">{t('p3.demo.needPush')}</p>}
        <div className="mt-2"><Switch label={t('p3.demo.inapp')} checked={sim} onChange={setSim} /></div>
      </DemoPanel>
      {demo && sim && <p className="text-caption font-semibold text-watch">{t('p3.demo.simBadge')}</p>}

      {pollErr && <ErrorBox error={pollErr} onRetry={() => { void poll() }} />}

      <h2 className="text-h2 text-ink">{t('p3.places.heading')}</h2>
      <ul className="space-y-3">
        {places.map((p) => {
          const s = status.find((x) => x.id === p.id)
          const isMine = !!mineP && p.id === mineP.id
          const lvl = s ? watchLevel(s.level) : 'unknown'
          return (
            <li key={p.id}>
              <Card tone={lvl} aria-busy={!s && !loaded}>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="flex flex-wrap items-center gap-2 text-h3 text-ink">{nameOf(p)}
                      {isMine && <span className="rounded-full bg-brand-tint px-2 text-caption font-semibold text-brand">{t('p3.places.myPlace')}</span>}
                    </p>
                    <p className="text-caption text-muted">{streetOf(p.label)}</p>
                  </div>
                  {s && <RiskBadge level={lvl} size="md" label={t('p3.level.' + s.level)} suffix={demo && sim ? t('demo.simulated') : undefined} />}
                </div>
                {!s && !loaded && <div className="mt-3 space-y-2"><Skeleton w="90%" h={16} /><Skeleton w="60%" h={16} /></div>}
                {!s && loaded && <p className="mt-3 text-body-sm text-muted">{t('p3.places.noStatus')}</p>}
                {s && (
                  <div className="mt-3 space-y-2">
                    <Freshness meta={s.meta} />
                    <p className="text-base text-ink">{s.message}</p>
                    {(s.reasons ?? []).length > 0 && (
                      <div><p className="text-caption font-semibold text-muted">{t('p3.places.why')}</p>
                        <ul className="list-disc ps-5 text-body-sm text-ink">{(s.reasons ?? []).map((r, i) => <li key={i}>{r}</li>)}</ul></div>
                    )}
                    <p className="text-caption text-muted">{t('p3.places.nearby').replace('{n}', String(s.crossings_nearby ?? 0)).replace('{m}', String((s.alerts ?? []).length))}</p>
                    <div className="flex flex-wrap gap-2">
                      {(s.gauges ?? []).map((g) => <span key={g.id} className="inline-flex items-center gap-1.5 text-caption text-muted">{g.name} <StatusBadge status={g.status} /><GaugeChips g={g} /></span>)}
                    </div>
                  </div>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button variant="secondary" size="sm" icon={Volume2} disabled={!s} onClick={() => s && speak(`${nameOf(p)}. ${s.message}`, lang)}>{t('p3.places.read')}</Button>
                  <Button variant="secondary" size="sm" icon={Route} onClick={() => checkRoute(p)}>{t('p3.places.route')}</Button>
                  {!isMine && <IconButton icon={MoreHorizontal} label={t('p3.places.more')} onClick={() => setMenu(p)} />}
                </div>
              </Card>
            </li>
          )
        })}
      </ul>

      <Button variant="secondary" icon={Plus} onClick={() => setAddOpen(true)}>{t('p3.add.btn')}</Button>

      <button type="button" onClick={() => setReportOpen(true)}
        className="flex min-h-14 w-full items-center gap-3 rounded-lg border border-line bg-surface p-3 text-start shadow-card hover:bg-surface-2">
        <Megaphone aria-hidden size={24} className="shrink-0 text-brand" />
        <span className="min-w-0"><span className="block text-base font-semibold text-ink">{t('p3.report.row')}</span><span className="block text-caption text-muted">{t('p3.report.rowSub')}</span></span>
      </button>

      <AddPlaceSheet open={addOpen} onClose={() => setAddOpen(false)} onAdded={(p) => { const n = [...extra.filter((x) => x.id !== p.id), p]; setExtra(n); save(n) }} />
      <Sheet open={!!menu} onClose={() => setMenu(null)} title={menu?.label ?? ''}>
        {menu && <Button variant="secondary" full onClick={() => remove(menu)}>{t('p3.places.remove')}</Button>}
      </Sheet>
      <ReportSheet open={reportOpen} onClose={() => setReportOpen(false)} />
    </div>
  )
}

function AddPlaceSheet({ open, onClose, onAdded }: { open: boolean; onClose: () => void; onAdded: (p: WatchPlace) => void }) {
  const { t, lang } = useApp()
  const [name, setName] = useState<string>('Family')
  const [addr, setAddr] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null)
    try {
      const g = await api.geocode(addr)
      let p: WatchPlace
      try { p = await api.watchSave({ label: addr.trim() || name, lat: g.lat, lon: g.lon, lang }) }
      catch (e3) { if (e3 instanceof ApiError && e3.status === 404) throw new Error(t('p3.add.unavailable')); throw e3 }
      onAdded({ id: p.id, label: placeName(name, t) + ' · ' + streetOf(p.label), lat: p.lat, lon: p.lon, lang })
      toast(t('p3.add.added').replace('{name}', placeName(name, t))); setAddr(''); onClose()
    } catch (e2) { setErr(errText(e2, t('offline'))) } finally { setBusy(false) }
  }
  return (
    <Sheet open={open} onClose={onClose} title={t('p3.add.title')}>
      <form onSubmit={submit} className="space-y-4">
        <div><p className="mb-1 text-body-sm font-medium text-ink">{t('p3.add.name')}</p>
          <Segmented size="sm" label={t('p3.add.name')} value={name} onChange={setName} options={NAMES.map((n) => ({ value: n, label: t('nick.' + n) }))} className="flex-wrap" /></div>
        <Field label={t('p3.add.address')}><input className={inputCls} required value={addr} onChange={(e) => setAddr(e.target.value)} placeholder={t('p3.drive.fromHint')} autoComplete="street-address" /></Field>
        {err && <ErrorBox error={err} />}
        <Button type="submit" size="lg" full loading={busy} icon={BellRing}>{t('p3.add.submit')}</Button>
      </form>
    </Sheet>
  )
}
