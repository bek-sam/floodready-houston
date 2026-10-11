// My place + household + onboarding + demo mode (docs/ux/redesign-spec.md §3.4, §7).
// Everything persists on this device only; every storage access is wrapped in try/catch.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Profile } from '../api'
import type { Place } from '../ctx'

export interface Household {
  renter: boolean | null; hasCar: boolean | null
  medical: { dialysis: boolean; oxygen: boolean; powerDevice: boolean; other: string }
  mobility: 'none' | 'some' | 'wheelchair'
  ages: { kids: boolean; older: boolean }
  pets: boolean
}
export interface MyPlace extends Place { nickname: string; zip: string | null; savedAt: string }

export const DEFAULT_HOUSEHOLD: Household = {
  renter: null, hasCar: null,
  medical: { dialysis: false, oxygen: false, powerDevice: false, other: '' },
  mobility: 'none', ages: { kids: false, older: false }, pets: false,
}

export const KEYS = {
  place: 'floodready.place.v1', household: 'floodready.household.v1', onboarded: 'floodready.onboarded.v1',
  actionsDone: 'floodready.actionsDone.v1', demo: 'floodready.demo',
} as const

/** Safe storage helpers: return null / do nothing when storage is unavailable. */
export const store = {
  get(k: string, session = false): string | null {
    try { return (session ? sessionStorage : localStorage).getItem(k) } catch { return null }
  },
  set(k: string, v: string | null, session = false) {
    try { const s = session ? sessionStorage : localStorage; if (v === null) s.removeItem(k); else s.setItem(k, v) } catch { /* ignore */ }
  },
  json<T>(k: string, fallback: T): T {
    try { const v = JSON.parse(localStorage.getItem(k) || 'null'); return v ?? fallback } catch { return fallback }
  },
}

const KEEP_UPPER = /^(TX|N|S|E|W|NE|NW|SE|SW|US|FM|IH|SH|CR|PO|II|III|IV)$/
/** "5300 N BRAESWOOD BLVD, HOUSTON, TX, 77096" -> "5300 N Braeswood Blvd, Houston, TX, 77096" */
export function toTitleCase(s: string): string {
  if (!s || s !== s.toUpperCase()) return s
  return s.toLowerCase().replace(/[a-z0-9][a-z0-9'.-]*/g, (w) => {
    const up = w.toUpperCase()
    if (KEEP_UPPER.test(up)) return up
    if (/^\d/.test(w)) return w // 1st, 77096
    return w[0].toUpperCase() + w.slice(1)
  })
}
export const zipOf = (s?: string | null) => s?.match(/\b\d{5}\b/)?.[0] ?? null
/** Street part of an address, e.g. "5300 N Braeswood Blvd". */
export const streetOf = (s: string) => s.split(',')[0].trim()

/** Same profile everywhere (Prepare, Ask, /plan, /profile). */
export function toProfile(h: Household, place: MyPlace | Place | null, lang: string): Profile {
  const m = h.medical
  const medical = [m.dialysis && 'dialysis', m.oxygen && 'oxygen', m.powerDevice && 'power device', m.other.trim()].filter(Boolean) as string[]
  return {
    language: lang, age_group: h.ages.older ? 'senior' : 'adult', mobility: h.mobility, medical,
    has_car: h.hasCar ?? true, pets: h.pets, renter: h.renter ?? false, address: place?.label ?? '',
  }
}

function normalize(p: Place | MyPlace, prev: MyPlace | null): MyPlace {
  const label = toTitleCase(p.label)
  const nickname = ('nickname' in p && p.nickname) || prev?.nickname || 'Home'
  return { lat: p.lat, lon: p.lon, label, nickname, zip: zipOf(label), savedAt: new Date().toISOString() }
}

function validPlace(v: unknown): MyPlace | null {
  const p = v as MyPlace | null
  return p && typeof p.lat === 'number' && typeof p.lon === 'number' && typeof p.label === 'string' ? p : null
}
function loadHousehold(): Household {
  const v = store.json<Partial<Household>>(KEYS.household, {})
  return { ...DEFAULT_HOUSEHOLD, ...v, medical: { ...DEFAULT_HOUSEHOLD.medical, ...(v.medical ?? {}) }, ages: { ...DEFAULT_HOUSEHOLD.ages, ...(v.ages ?? {}) } }
}

/** Read ?demo=1 / ?demo=0 once, persist to sessionStorage, strip the param from the URL. */
function initDemo(): { demo: boolean; fromUrl: boolean } {
  let fromUrl = false
  try {
    const u = new URL(location.href)
    const d = u.searchParams.get('demo')
    if (d === '1' || d === '0') {
      store.set(KEYS.demo, d === '1' ? '1' : null, true)
      fromUrl = d === '1'
      u.searchParams.delete('demo')
      history.replaceState(history.state, '', u.pathname + u.search + u.hash)
    }
  } catch { /* ignore */ }
  return { demo: store.get(KEYS.demo, true) === '1', fromUrl }
}

export interface PlaceCtx {
  place: MyPlace | null; setPlace(p: Place | MyPlace | null): void
  household: Household; setHousehold(h: Household): void
  onboarded: boolean; finishOnboarding(): void
  demo: boolean; setDemo(on: boolean): void
  /** True when this page load came from ?demo=1 (onboarding is skipped). */
  demoFromUrl: boolean
}
const Ctx = createContext<PlaceCtx | null>(null)

export function PlaceProvider({ children }: { children: ReactNode }) {
  const [init] = useState(initDemo)
  const [place, setPlaceState] = useState<MyPlace | null>(() => validPlace(store.json(KEYS.place, null)))
  const [household, setHouseholdState] = useState<Household>(loadHousehold)
  const [onboarded, setOnboarded] = useState(() => store.get(KEYS.onboarded) === '1')
  const [demo, setDemoState] = useState(init.demo)

  const setPlace = useCallback((p: Place | MyPlace | null) => {
    setPlaceState((prev) => {
      const next = p ? normalize(p, prev) : null
      store.set(KEYS.place, next ? JSON.stringify(next) : null)
      return next
    })
  }, [])
  const setHousehold = useCallback((h: Household) => { setHouseholdState(h); store.set(KEYS.household, JSON.stringify(h)) }, [])
  const finishOnboarding = useCallback(() => { setOnboarded(true); store.set(KEYS.onboarded, '1') }, [])
  const setDemo = useCallback((on: boolean) => { setDemoState(on); store.set(KEYS.demo, on ? '1' : null, true) }, [])

  // Keep tabs in sync when another tab changes the saved place.
  useEffect(() => {
    const f = (e: StorageEvent) => {
      if (e.key === KEYS.place) setPlaceState(validPlace(store.json(KEYS.place, null)))
      if (e.key === KEYS.household) setHouseholdState(loadHousehold())
    }
    window.addEventListener('storage', f)
    return () => window.removeEventListener('storage', f)
  }, [])

  const value = useMemo<PlaceCtx>(() => ({
    place, setPlace, household, setHousehold, onboarded, finishOnboarding, demo, setDemo, demoFromUrl: init.fromUrl,
  }), [place, setPlace, household, setHousehold, onboarded, finishOnboarding, demo, setDemo, init.fromUrl])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function usePlace(): PlaceCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error('usePlace must be used inside <PlaceProvider>')
  return c
}
/** Demo mode (session-scoped). Gate every demo-only control on `demo`. */
export function useDemoMode(): { demo: boolean; setDemo: (on: boolean) => void } {
  const { demo, setDemo } = usePlace()
  return { demo, setDemo }
}

/** Short household summary keys for chips, e.g. ["hh.rents","hh.noCar","hh.dialysis"]. */
export function householdChips(h: Household): string[] {
  const out: string[] = []
  if (h.renter === true) out.push('hh.rents'); if (h.renter === false) out.push('hh.owns')
  if (h.hasCar === false) out.push('hh.noCar'); if (h.hasCar === true) out.push('hh.car')
  if (h.medical.dialysis) out.push('hh.dialysis'); if (h.medical.oxygen) out.push('hh.oxygen')
  if (h.medical.powerDevice) out.push('hh.power'); if (h.mobility !== 'none') out.push('hh.mobility')
  if (h.ages.kids) out.push('hh.kids'); if (h.ages.older) out.push('hh.older'); if (h.pets) out.push('hh.pets')
  return out
}

/** Preset nicknames are stored in English ("Home") and shown localized; custom names are shown as typed. */
export const NICKNAMES = ['Home', 'Family', 'Work', 'Other'] as const
export function placeName(nickname: string | null | undefined, t: (k: string) => string): string {
  if (!nickname) return t('nick.Home')
  const k = 'nick.' + nickname
  const v = t(k)
  return v === k ? nickname : v
}
