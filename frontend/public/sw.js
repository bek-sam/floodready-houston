/* FloodReady service worker: shell precache, stale-while-revalidate for safe GET APIs, push. */
const BUILD = '__BUILD__' // replaced at build time by vite.config.ts
const SHELL = 'fr-shell-' + BUILD
const RUNTIME = 'fr-runtime-' + BUILD
const PRECACHE = ['/', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png', '/apple-touch-icon.png']
const ASSETS = [] // __ASSETS__ replaced at build time with dist/assets/* (lazy page chunks) so pages work offline
const CACHEABLE_API = [/^\/api\/replay\//, /^\/api\/civic/, /^\/api\/insurance\/countdown/, /^\/api\/route-check\/demo/, /^\/api\/shelters/, /^\/api\/outlook/]

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(PRECACHE).then(() => Promise.all(ASSETS.map((u) => c.add(u).catch(() => {}))))).then(() => self.skipWaiting()))
})
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== SHELL && k !== RUNTIME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

const offlineJson = () => new Response(JSON.stringify({ offline: true }), { status: 503, headers: { 'Content-Type': 'application/json' } })

// Always resolves to a Response (cache hit, network, or offline JSON).
async function swr(req, cacheName) {
  const cache = await caches.open(cacheName)
  const hit = await cache.match(req, { ignoreVary: true })
  const net = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res }).catch(() => null)
  if (hit) return hit
  return (await net) || offlineJson()
}

// Network first, cache fallback: users always get the newest shell/assets when online.
async function networkFirst(req, cacheName, fallbackKey) {
  const cache = await caches.open(cacheName)
  try {
    const res = await fetch(req)
    if (res.ok) cache.put(fallbackKey || req, res.clone())
    return res
  } catch {
    // ignoreVary: a `Vary: Origin` header must not hide a cached asset offline.
    // Only navigations fall back to the HTML shell; serving HTML for a .js/.css request blanks the app.
    const hit = await cache.match(fallbackKey || req, { ignoreVary: true })
    if (hit) return hit
    if (req.mode === 'navigate') return (await caches.match('/', { ignoreVary: true })) || new Response('Offline', { status: 503 })
    return new Response('', { status: 504, statusText: 'Offline' })
  }
}

self.addEventListener('fetch', (e) => {
  const req = e.request
  if (req.method !== 'GET') return // never cache POST etc.
  const url = new URL(req.url)
  if (url.origin !== location.origin) return // map tiles etc. go straight to the network
  if (url.pathname.startsWith('/api/')) {
    if (CACHEABLE_API.some((r) => r.test(url.pathname))) e.respondWith(swr(req, RUNTIME))
    return
  }
  if (req.mode === 'navigate') { e.respondWith(networkFirst(req, SHELL, '/')); return }
  e.respondWith(networkFirst(req, SHELL))
})

self.addEventListener('push', (e) => {
  let d = {}
  try { d = e.data ? e.data.json() : {} } catch { d = { body: e.data ? e.data.text() : '' } }
  e.waitUntil(self.registration.showNotification(d.title || 'FloodReady Houston', {
    body: d.body || '', tag: d.tag, icon: '/icon-192.png', badge: '/icon-192.png',
    requireInteraction: d.level === 'warning', data: { url: d.url || '/#watch' },
  }))
})

self.addEventListener('notificationclick', (e) => {
  e.notification.close()
  const target = new URL(e.notification.data?.url || '/', self.location.origin).href
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((cs) => {
    for (const c of cs) if (c.url.startsWith(self.location.origin) && 'focus' in c) { c.navigate?.(target); return c.focus() }
    return self.clients.openWindow(target)
  }))
})
