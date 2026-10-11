import { createContext, useContext } from 'react'
import type { LatLon } from './api'
import type { MyPlace } from './state/place'

export interface Place extends LatLon { label: string }
export interface Ctx {
  lang: string
  t: (key: string) => string
  setLang: (code: string) => void
  dark: boolean
  setDark: (dark: boolean) => void
  /** My place (persisted). Same object as usePlace().place; kept here so older components keep compiling. */
  place: MyPlace | null
  setPlace: (p: Place | MyPlace | null) => void
}
export const AppCtx = createContext<Ctx>(null as unknown as Ctx)
export const useApp = () => useContext(AppCtx)
export const HOUSTON: LatLon = { lat: 29.7604, lon: -95.3698 }

// The place/household/demo state lives in src/state/place.tsx.
export { usePlace, useDemoMode, toProfile, toTitleCase, type MyPlace, type Household } from './state/place'
