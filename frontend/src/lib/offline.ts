import { useEffect, useState } from 'react'
import { store } from '../state/place'

export function useOnline(): boolean {
  const [on, setOn] = useState(() => navigator.onLine)
  useEffect(() => {
    const a = () => setOn(true), b = () => setOn(false)
    window.addEventListener('online', a); window.addEventListener('offline', b)
    return () => { window.removeEventListener('online', a); window.removeEventListener('offline', b) }
  }, [])
  return on
}

export const HOME_CACHE = 'floodready.homeCache.v1'
export const EVAC_CACHE = 'floodready.evacCache.v1'
export const PLAN_AT = 'floodready.lastPlanAt.v1'
export const WATCH_CACHE = 'floodready.watchCache.v1'

/** Time of the newest saved home result (ms), or null. */
export function lastHomeAt(): number | null {
  const c = store.json<Record<string, { at?: number }>>(HOME_CACHE, {})
  const ats = Object.values(c).map((x) => x?.at).filter((a): a is number => typeof a === 'number')
  return ats.length ? Math.max(...ats) : null
}

export function fmtAt(ts: number, lang: string): string {
  try { return new Date(ts).toLocaleString(lang, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) } catch { return new Date(ts).toLocaleString() }
}
