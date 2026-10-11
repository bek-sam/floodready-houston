import { useEffect, useMemo, useState } from 'react'
import { api, type Alerts, type Outlook, type Risk } from '../api'
import { AppCtx } from '../ctx'
import { tr } from '../i18n'
import { alertLevel, fill, isFloodAlert } from '../lib/summary'
import { maxLevel, type Level } from '../lib/levels'
import { RiskBadge } from '../components/ds'

const LANGS = ['en', 'es', 'vi', 'zh', 'ar']

/** Embeddable card for a fixed place (#widget?lat=..&lon=..&lang=en). No personal data, no storage writes, no nav. */
export default function Widget() {
  const p = useMemo(() => new URLSearchParams(location.pathname.startsWith('/widget') ? location.search : location.hash.replace(/^#widget\??/, '')), [])
  const lat = Number(p.get('lat')), lon = Number(p.get('lon'))
  const ok = p.get('lat') !== null && p.get('lon') !== null && Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180
  const lang = LANGS.includes(p.get('lang') ?? '') ? p.get('lang')! : 'en'
  const label = (p.get('label') ?? '').replace(/[<>]/g, '').slice(0, 60)
  const t = (k: string) => tr(lang, k)
  const [d, setD] = useState<{ alerts: Alerts | null; risk: Risk | null; outlook: Outlook | null; done: boolean }>({ alerts: null, risk: null, outlook: null, done: false })

  useEffect(() => {
    const dark = (() => { try { return matchMedia('(prefers-color-scheme: dark)').matches } catch { return false } })()
    document.documentElement.dataset.theme = p.get('theme') === 'dark' || (dark && p.get('theme') !== 'light') ? 'dark' : 'light'
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    document.title = t('p15.w.title')
    if (!ok) return
    const ll = { lat, lon }
    Promise.allSettled([api.alerts(ll), api.risk(ll), api.outlook(ll)]).then(([a, r, o]) =>
      setD({ alerts: a.status === 'fulfilled' ? a.value : null, risk: r.status === 'fulfilled' ? r.value : null, outlook: o.status === 'fulfilled' ? o.value : null, done: true }))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const ctx = useMemo(() => ({ lang, t, setLang: () => {}, dark: false, setDark: () => {}, place: null, setPlace: () => {} }), [lang]) // eslint-disable-line react-hooks/exhaustive-deps
  const flood = (d.alerts?.alerts ?? []).filter((a) => isFloodAlert(a.event))
  const level: Level = !d.done ? 'unknown' : !d.alerts ? 'unknown' : flood.length ? maxLevel(...flood.map((a) => alertLevel(a.event))) : 'normal'
  const cat = d.outlook?.day1?.category
  const open = `${location.origin}/#home`
  return (
    <AppCtx.Provider value={ctx as never}>
      <main className="mx-auto min-h-dvh max-w-[400px] bg-bg p-3 text-ink">
        <section className="rounded-lg border border-line bg-surface p-4 shadow-card" aria-live="polite">
          <h1 className="text-h3 text-ink">{t('p15.w.title')}{label && <span className="block text-body-sm font-normal text-muted">{label}</span>}</h1>
          {!ok ? <p className="mt-2 text-body-sm">{t('p15.w.bad')}</p> : !d.done ? <p className="mt-2 text-body-sm text-muted">{t('p15.w.checking')}…</p>
            : !d.alerts ? <p className="mt-2 text-body-sm">{t('p15.w.fail')}</p> : (
              <div className="mt-2 space-y-2">
                <RiskBadge level={level} label={t('level.' + level)} />
                <p className="text-body-sm">{flood.length ? fill(t, 'p15.w.alerts', { n: flood.length }) : t('p15.w.none')}</p>
                {flood.slice(0, 2).map((a, i) => <p key={i} className="text-body-sm font-semibold">{a.event}</p>)}
                {cat && <p className="text-body-sm text-muted">{fill(t, 'p15.w.outlook', { c: d.outlook?.day1?.label || cat })}</p>}
                {d.risk?.fema_zone && <p className="text-caption text-muted">{fill(t, 'p15.w.zone', { z: d.risk.fema_zone })}</p>}
              </div>
            )}
          <a href={open} target="_top" className="mt-3 inline-flex min-h-11 items-center text-body-sm font-semibold text-brand underline underline-offset-2">{t('p15.w.open')}</a>
          <p className="mt-2 text-caption text-muted">{t('p15.w.attr')}</p>
        </section>
      </main>
    </AppCtx.Provider>
  )
}
