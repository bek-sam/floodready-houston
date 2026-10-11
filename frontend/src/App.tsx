import { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AppCtx } from './ctx'
import { tr } from './i18n'
import ErrorBoundary from './components/ErrorBoundary'
import { PlaceProvider, placeName, store, usePlace } from './state/place'
import { Toaster, toast } from './components/ds'
import { ShellCtx } from './components/shell/ShellContext'
import { parseHash } from './components/shell/nav'
import { EmergencyStrip } from './components/shell/EmergencyStrip'
import { Header } from './components/shell/Header'
import { Sidebar } from './components/shell/Sidebar'
import { BottomNav } from './components/shell/BottomNav'
import { OfflineBanner } from './components/shell/OfflineBanner'
import { MyPlaceSheet } from './components/shell/MyPlaceSheet'
import { HouseholdSheet } from './components/shell/HouseholdSheet'
import { MoreSheet } from './components/shell/MoreSheet'
import { LanguageSheet } from './components/shell/LanguageSheet'

const PAGES = {
  home: lazy(() => import('./pages/Home')),
  alerts: lazy(() => import('./pages/Watch')),
  drive: lazy(() => import('./pages/Drive')),
  prepare: lazy(() => import('./pages/Prepare')),
  ask: lazy(() => import('./pages/Ask')),
  replay: lazy(() => import('./pages/Replay')),
  recover: lazy(() => import('./pages/Recover')),
  civic: lazy(() => import('./pages/Civic')),
  settings: lazy(() => import('./pages/Settings')),
  about: lazy(() => import('./pages/About')),
  status: lazy(() => import('./pages/Status')),
  judge: lazy(() => import('./pages/Judge')),
  compare: lazy(() => import('./pages/Compare')),
} as const
type Route = keyof typeof PAGES
const Welcome = lazy(() => import('./pages/Welcome'))

const Spinner = () => (
  <div role="status" aria-label="Loading" className="flex justify-center py-16">
    <span className="h-8 w-8 animate-spin rounded-full border-4 border-line border-t-brand" />
  </div>
)

export default function App() {
  return <PlaceProvider><Shell /></PlaceProvider>
}

function Shell() {
  const pc = usePlace()
  const { place, setPlace, onboarded, demo, setDemo } = pc
  const [hash, setHash] = useState(() => parseHash())
  const [lang, setLang] = useState(() => store.get('lang') || 'en')
  const [dark, setDark] = useState(() => {
    const s = store.get('theme')
    if (s) return s === 'dark'
    try { return matchMedia('(prefers-color-scheme: dark)').matches } catch { return false }
  })
  const [sheet, setSheet] = useState<null | 'place' | 'household' | 'more' | 'lang'>(null)
  const [danger, setDanger] = useState<string | null>(null)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    store.set('theme', dark ? 'dark' : 'light')
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#131C26' : '#0B4F94')
  }, [dark])
  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    store.set('lang', lang)
  }, [lang])
  useEffect(() => {
    const f = () => { setHash(parseHash()); setSheet(null) }
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [])

  const route: Route = hash.route in PAGES ? (hash.route as Route) : 'home'
  const showWelcome = hash.route === 'welcome' || (!onboarded && !demo)

  useEffect(() => {
    const key = showWelcome ? 'app' : 'nav.' + route
    document.title = showWelcome ? tr(lang, 'app') : `${tr(lang, key)} · ${tr(lang, 'app')}`
  }, [route, lang, showWelcome])
  // Move focus to main on navigation (not on first load) so screen readers land on the new page.
  const first = useRef(true)
  useEffect(() => {
    if (first.current) { first.current = false; return }
    const m = document.getElementById('main')
    m?.focus({ preventScroll: true }); window.scrollTo(0, 0)
  }, [route])

  const [online, setOnline] = useState(navigator.onLine)
  const [installEv, setInstallEv] = useState<{ prompt: () => Promise<void> } | null>(null)
  useEffect(() => {
    const on = () => setOnline(true), off = () => setOnline(false)
    const bip = (e: Event) => { e.preventDefault(); setInstallEv(e as unknown as { prompt: () => Promise<void> }) }
    window.addEventListener('online', on); window.addEventListener('offline', off)
    window.addEventListener('beforeinstallprompt', bip)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); window.removeEventListener('beforeinstallprompt', bip) }
  }, [])
  const install = installEv ? () => { installEv.prompt().catch(() => {}); setInstallEv(null) } : undefined

  const ctx = useMemo(() => ({ lang, t: (k: string) => tr(lang, k), setLang, dark, setDark, place, setPlace }), [lang, dark, place, setPlace])
  const t = ctx.t
  const shell = useMemo(() => ({
    openPlaceSheet: () => setSheet('place'), openHouseholdSheet: () => setSheet('household'), setDanger,
  }), [])

  // Logo long-press (2s) turns on demo mode and opens the Judge page (undocumented escape hatch, §6.8).
  const press = useRef<{ timer?: ReturnType<typeof setTimeout>; fired?: boolean }>({})
  const startPress = useCallback(() => {
    press.current.fired = false
    press.current.timer = setTimeout(() => {
      press.current.fired = true
      setDemo(true)
      toast(tr(lang, 'demo.on'))
      location.hash = '#judge'
    }, 2000)
  }, [setDemo, lang])
  const endPress = () => clearTimeout(press.current.timer)
  const logoProps = {
    onPointerDown: startPress, onPointerUp: endPress, onPointerLeave: endPress, onPointerCancel: endPress,
    onClick: (e: React.MouseEvent) => { if (press.current.fired) e.preventDefault() },
    onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
  }

  const Active = PAGES[route]
  const nick = place ? placeName(place.nickname, t) : undefined

  return (
    <AppCtx.Provider value={ctx}>
      <ShellCtx.Provider value={shell}>
        {demo && <div aria-hidden className="pointer-events-none fixed inset-x-0 top-0 z-[1200] h-0.5 bg-watch" />}
        {showWelcome ? (
          <Suspense fallback={<Spinner />}>
            <Welcome onDone={() => { location.hash = '#home'; setHash(parseHash('#home')) }} />
          </Suspense>
        ) : (
          <>
            <a href="#main" onClick={(e) => { e.preventDefault(); const m = document.getElementById('main'); m?.focus(); m?.scrollIntoView() }}
              className="sr-only focus:not-sr-only focus:fixed focus:start-2 focus:top-2 focus:z-[2000] focus:rounded-md focus:bg-surface focus:p-3 focus:text-ink focus:underline">
              {t('shell.skip')}
            </a>
            <div className="md:flex">
              <Sidebar route={route} logoProps={logoProps} />
              <div className="flex min-h-dvh min-w-0 flex-1 flex-col">
                <EmergencyStrip dangerEvent={danger} placeName={nick} />
                <Header onPlace={() => setSheet('place')} onLang={() => setSheet('lang')} onMore={() => setSheet('more')} onInstall={install} logoProps={logoProps} />
                {!online && <OfflineBanner />}
                <main id="main" tabIndex={-1}
                  className={`mx-auto w-full flex-1 px-4 pt-4 md:pt-6 pb-[calc(6rem+env(safe-area-inset-bottom))] outline-none md:px-6 md:pb-10 ${route === 'home' ? 'max-w-[1040px]' : 'max-w-[960px]'}`}>
                  <ErrorBoundary key={route}><Suspense fallback={<Spinner />}><Active /></Suspense></ErrorBoundary>
                </main>
              </div>
            </div>
            <BottomNav route={route} />
          </>
        )}
        <MyPlaceSheet open={sheet === 'place'} onClose={() => setSheet(null)} onEditHousehold={() => setSheet('household')} />
        <HouseholdSheet open={sheet === 'household'} onClose={() => setSheet(null)} />
        <MoreSheet open={sheet === 'more'} onClose={() => setSheet(null)} route={route} onInstall={install} />
        <LanguageSheet open={sheet === 'lang'} onClose={() => setSheet(null)} />
        <Toaster />
      </ShellCtx.Provider>
    </AppCtx.Provider>
  )
}
