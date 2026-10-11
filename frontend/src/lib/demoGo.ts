import { store } from '../state/place'

/** Judge page "Go" buttons store the step number here (sessionStorage); the target page reads it once. */
export const DEMO_GO_KEY = 'floodready.demoGo'

/** True when the Judge page just sent the user here for `step`. Does not clear (safe in render/StrictMode). */
export const peekDemoGo = (step: number) => store.get(DEMO_GO_KEY, true) === String(step)
export const clearDemoGo = () => store.set(DEMO_GO_KEY, null, true)
