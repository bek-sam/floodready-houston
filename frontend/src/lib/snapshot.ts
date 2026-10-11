// Detects offline-demo snapshot responses (header X-FloodReady-Snapshot only; meta.freshness "snapshot" also marks legit static datasets like crossings) on /api fetches.
type Info = { date: string | null }
let info: Info | null = null
const subs = new Set<() => void>()
export const getSnapshot = () => info
export function subscribeSnapshot(fn: () => void) { subs.add(fn); return () => { subs.delete(fn) } }
function mark(date: string | null) {
  if (info && info.date === date) return
  info = { date: date || info?.date || null }
  subs.forEach((f) => f())
}

export function installSnapshotWatcher() {
  if (typeof window === 'undefined' || (window as unknown as { __snapW?: boolean }).__snapW) return
  ;(window as unknown as { __snapW?: boolean }).__snapW = true
  const orig = window.fetch.bind(window)
  window.fetch = async (input, init) => {
    const res = await orig(input, init)
    try {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
      if (url.includes('/api/') && !url.includes('/api/voice') && !url.includes('/api/demo/')) {
        if (res.headers.get('X-FloodReady-Snapshot')) mark(res.headers.get('X-FloodReady-Snapshot-Date'))
      }
    } catch { /* never break a request */ }
    return res
  }
}
