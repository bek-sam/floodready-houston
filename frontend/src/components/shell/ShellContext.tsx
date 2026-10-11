import { createContext, useContext } from 'react'

export interface Shell {
  /** Open the My place sheet (change address, household, watched places). */
  openPlaceSheet: () => void
  /** Open the household editor sheet directly. */
  openHouseholdSheet: () => void
  /** Escalate the 911 strip: pass the NWS event (e.g. "Flash Flood Emergency") when Right now = Danger, or null to calm it. */
  setDanger: (event: string | null) => void
}
const noop = () => {}
export const ShellCtx = createContext<Shell>({ openPlaceSheet: noop, openHouseholdSheet: noop, setDanger: noop })
export const useShell = () => useContext(ShellCtx)
