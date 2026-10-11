// 3D storm replay (maplibre-gl, no token). Water height is ILLUSTRATIVE: the nearest gauge's
// stage above its action stage, scaled. Gauges are columns colored by flood category.
import { useEffect, useMemo, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

maplibregl.setWorkerUrl(workerUrl)
import { LocateFixed } from 'lucide-react'
import { statusFor, type ReplayGauge } from '../../api'
import { useApp } from '../../ctx'
import { mapColor } from '../ui'
import { Button } from '../ds'

type Pt = { lat: number; lon: number }
type FC = GeoJSON.FeatureCollection<GeoJSON.Geometry, Record<string, unknown>>
const EMPTY: FC = { type: 'FeatureCollection', features: [] }
const MAX_FEATURES = 300
const FT_TO_M = 0.3048
const WATER_SCALE = 12 // visual exaggeration of (stage - action) in meters
const STYLE = 'https://tiles.openfreemap.org/styles/liberty'

export function webglOk(): boolean {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')) } catch { return false }
}

function valueAt(g: ReplayGauge, ms: number): number | null {
  const s = g.series
  let lo = 0, hi = s.length - 1, ans = -1
  while (lo <= hi) { const m = (lo + hi) >> 1; if (Date.parse(s[m].t) <= ms) { ans = m; lo = m + 1 } else hi = m - 1 }
  return ans < 0 ? null : s[ans].stage_ft
}
const dist2 = (a: Pt, b: Pt) => (a.lat - b.lat) ** 2 + ((a.lon - b.lon) * Math.cos(a.lat * Math.PI / 180)) ** 2
const square = (lat: number, lon: number, r: number): GeoJSON.Polygon => {
  const dl = r / 111320, dn = r / (111320 * Math.cos(lat * Math.PI / 180))
  return { type: 'Polygon', coordinates: [[[lon - dn, lat - dl], [lon + dn, lat - dl], [lon + dn, lat + dl], [lon - dn, lat + dl], [lon - dn, lat - dl]]] }
}
const disc = (lat: number, lon: number, r: number): GeoJSON.Polygon => {
  const ring: [number, number][] = []
  for (let i = 0; i <= 24; i++) { const a = (i / 24) * 2 * Math.PI; ring.push([lon + (r * Math.cos(a)) / (111320 * Math.cos(lat * Math.PI / 180)), lat + (r * Math.sin(a)) / 111320]) }
  return { type: 'Polygon', coordinates: [ring] }
}
function centroid(g: GeoJSON.Geometry): Pt | null {
  const pts: number[][] = []
  const walk = (c: unknown): void => { if (Array.isArray(c) && typeof c[0] === 'number') pts.push(c as number[]); else if (Array.isArray(c)) c.forEach(walk) }
  if ('coordinates' in g) walk(g.coordinates)
  if (!pts.length) return null
  let x = 0, y = 0
  pts.forEach((p) => { x += p[0]; y += p[1] })
  return { lon: x / pts.length, lat: y / pts.length }
}

export interface Replay3DProps {
  eventId: string; gauges: ReplayGauge[]; cur: number; playing: boolean
  selectedId?: string; onSelect: (id: string) => void; place?: Pt | null
  onUnsupported: () => void
}

export default function Replay3D({ eventId, gauges, cur, playing, selectedId, onSelect, place, onUnsupported }: Replay3DProps) {
  const { t } = useApp()
  const box = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const [orbit, setOrbit] = useState(() => !matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [extent, setExtent] = useState<FC | null>(null)
  const [extentTried, setExtentTried] = useState(false)
  const reduced = useMemo(() => matchMedia('(prefers-reduced-motion: reduce)').matches, [])
  const cb = useRef({ onSelect, onUnsupported }); cb.current = { onSelect, onUnsupported }

  const center = useMemo(() => {
    if (!gauges.length) return { lat: 29.76, lon: -95.37 }
    return { lat: gauges.reduce((a, g) => a + g.lat, 0) / gauges.length, lon: gauges.reduce((a, g) => a + g.lon, 0) / gauges.length }
  }, [gauges])
  // Harvey extent polygons for the current camera view (tolerate 404 / errors: fall back to discs).
  // The backend clips polygons to the requested bbox, so the result is trusted as is.
  const [camBox, setCamBox] = useState('')
  useEffect(() => {
    setExtent(null); setExtentTried(false)
    if (!/harvey/i.test(eventId) || !camBox) { setExtentTried(!/harvey/i.test(eventId)); return }
    const ac = new AbortController()
    const timer = window.setTimeout(() => {
      fetch(`/api/harvey/extent?bbox=${camBox}&limit=${MAX_FEATURES}`, { signal: ac.signal })
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => {
          if (!j || !Array.isArray(j.features)) return
          const feats = (j.features as FC['features']).slice(0, MAX_FEATURES)
          setExtent({ type: 'FeatureCollection', features: feats })
        })
        .catch(() => {}).finally(() => { if (!ac.signal.aborted) setExtentTried(true) })
    }, 500)
    return () => { window.clearTimeout(timer); ac.abort() }
  }, [eventId, camBox])

  // Nearest-gauge index per extent feature, computed once.
  const waterBase = useMemo<FC>(() => {
    if (!gauges.length) return EMPTY
    if (extent) {
      return { type: 'FeatureCollection', features: extent.features.map((f) => {
        const c = centroid(f.geometry); let gi = 0
        if (c) { let b = Infinity; gauges.forEach((g, i) => { const d = dist2(c, g); if (d < b) { b = d; gi = i } }) }
        return { ...f, properties: { ...f.properties, gi, h: 0 } }
      }) }
    }
    if (/harvey/i.test(eventId) && !extentTried) return EMPTY
    return { type: 'FeatureCollection', features: gauges.map((g, i) => ({ type: 'Feature' as const, geometry: disc(g.lat, g.lon, 900), properties: { gi: i, h: 0 } })) }
  }, [extent, gauges, eventId, extentTried])

  // Create the map once.
  useEffect(() => {
    if (!box.current) return
    if (!webglOk()) { setFailed(true); cb.current.onUnsupported(); return }
    let map: maplibregl.Map
    try {
      map = new maplibregl.Map({ container: box.current, style: STYLE, center: [center.lon, center.lat], zoom: 11.3, pitch: 60, bearing: -20, maxPitch: 80, attributionControl: { compact: true }, canvasContextAttributes: { antialias: true } })
    } catch { setFailed(true); cb.current.onUnsupported(); return }
    mapRef.current = map
    if (import.meta.env.DEV) (window as unknown as { __m3d?: unknown }).__m3d = map
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    map.on('error', (e) => { if (import.meta.env.DEV) console.warn('[3d]', String(e.error?.message ?? e)) })
    map.on('load', () => {
      try {
        map.addSource('dem', { type: 'raster-dem', tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'], encoding: 'terrarium', tileSize: 256, maxzoom: 14 })
        map.setTerrain({ source: 'dem', exaggeration: 1.2 })
      } catch { /* terrain optional */ }
      const layers = map.getStyle().layers ?? []
      const bld = layers.find((l) => l.id === 'building-3d' || (l.type === 'fill-extrusion'))
      if (!bld) {
        const src = Object.keys(map.getStyle().sources).find((s) => s !== 'dem') ?? 'openmaptiles'
        map.addLayer({ id: 'building-3d', type: 'fill-extrusion', source: src, 'source-layer': 'building', minzoom: 13,
          paint: { 'fill-extrusion-color': '#cfd3d9', 'fill-extrusion-opacity': 0.8,
            'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 8], 'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0] } })
      } else if (bld.type === 'fill-extrusion') {
        map.setPaintProperty(bld.id, 'fill-extrusion-opacity', 0.85)
      }
      map.addSource('water', { type: 'geojson', data: EMPTY })
      map.addLayer({ id: 'water-3d', type: 'fill-extrusion', source: 'water',
        paint: { 'fill-extrusion-color': '#0f55b8', 'fill-extrusion-opacity': 0.45, 'fill-extrusion-height': ['get', 'h'], 'fill-extrusion-base': 0 } })
      map.addSource('gauges', { type: 'geojson', data: EMPTY })
      map.addLayer({ id: 'gauge-3d', type: 'fill-extrusion', source: 'gauges',
        paint: { 'fill-extrusion-color': ['get', 'color'], 'fill-extrusion-opacity': 0.95, 'fill-extrusion-height': ['get', 'h'], 'fill-extrusion-base': 0 } })
      map.on('click', 'gauge-3d', (e) => { const id = e.features?.[0]?.properties?.id; if (id) cb.current.onSelect(String(id)) })
      map.on('mouseenter', 'gauge-3d', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'gauge-3d', () => { map.getCanvas().style.cursor = '' })
      const upd = () => {
        const bb = map.getBounds(); const px = (bb.getEast() - bb.getWest()) * 0.15, py = (bb.getNorth() - bb.getSouth()) * 0.15 // ~1.3x view
        const box = [bb.getWest() - px, bb.getSouth() - py, bb.getEast() + px, bb.getNorth() + py].map((n) => n.toFixed(3)).join(',')
        setCamBox((o) => (o === box ? o : box))
      }
      let tm = 0
      map.on('moveend', () => { window.clearTimeout(tm); tm = window.setTimeout(upd, 400) })
      upd()
      // gauge label on hover/tap
      const pop = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 })
      const show = (e: maplibregl.MapLayerMouseEvent) => { const p = e.features?.[0]?.properties; if (p) pop.setLngLat(e.lngLat).setText(`${p.name}: ${Number(p.v).toFixed(1)} ft`).addTo(map) }
      map.on('mousemove', 'gauge-3d', show)
      map.on('mouseleave', 'gauge-3d', () => pop.remove())
      map.on('click', 'gauge-3d', show)
      setReady(true)
    })
    return () => { setReady(false); mapRef.current = null; try { map.remove() } catch { /* already disposed */ } }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recenter when the event (gauge set) changes.
  useEffect(() => { if (ready && mapRef.current) mapRef.current.easeTo({ center: [center.lon, center.lat], duration: reduced ? 0 : 1200 }) }, [center.lat, center.lon, ready, reduced])

  // Update water + gauge columns when time changes.
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    const vals = gauges.map((g) => valueAt(g, cur))
    const hs = gauges.map((g, i) => { const v = vals[i]; const a = g.flood_stages.action; return v == null || a == null ? 0 : Math.max(0, v - a) * FT_TO_M * WATER_SCALE })
    const w = map.getSource('water') as maplibregl.GeoJSONSource | undefined
    w?.setData({ ...waterBase, features: waterBase.features.map((f) => ({ ...f, properties: { ...f.properties, h: hs[(f.properties?.gi as number) ?? 0] ?? 0 } })) })
    const gs = map.getSource('gauges') as maplibregl.GeoJSONSource | undefined
    gs?.setData({ type: 'FeatureCollection', features: gauges.map((g, i) => ({
      type: 'Feature' as const, geometry: square(g.lat, g.lon, g.id === selectedId ? 260 : 200),
      properties: { id: g.id, name: g.name, v: vals[i] ?? 0, h: 180 + Math.max(0, (vals[i] ?? 0) - (g.flood_stages.action ?? vals[i] ?? 0)) * FT_TO_M * 60, color: mapColor(statusFor(vals[i], g.flood_stages)) } })) })
  }, [ready, cur, gauges, waterBase, selectedId])

  // Auto-orbit while playing (not for reduced motion).
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map || !playing || !orbit || reduced) return
    let raf = 0, last = performance.now()
    const tick = (n: number) => { const dt = n - last; last = n; map.setBearing(map.getBearing() + dt * 0.006); raf = requestAnimationFrame(tick) }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [ready, playing, orbit, reduced])

  const fly = () => {
    if (!place || !mapRef.current) return
    mapRef.current.flyTo({ center: [place.lon, place.lat], zoom: 15.2, pitch: 65, bearing: -30, duration: reduced ? 0 : 3000, essential: false })
  }

  if (failed) return <div role="alert" className="rounded-lg border border-line bg-surface-2 p-4 text-body-sm text-ink">{t('p7.nowebgl')}</div>
  const noExtent = extentTried && /harvey/i.test(eventId) && !extent

  return (
    <div className="space-y-2">
      <div className="relative h-80 max-h-[60vh] overflow-hidden rounded-lg border border-line sm:h-[32rem]">
        <div ref={box} role="application" aria-label={t('p7.label')} style={{ position: 'absolute', inset: 0 }} />
        {!ready && <div className="absolute inset-0 grid place-items-center bg-surface-2 text-body-sm text-muted" aria-live="polite">{t('p7.loading')}</div>}
        <div className="pointer-events-none absolute inset-x-2 bottom-2 rounded-md bg-surface/90 px-3 py-1.5 text-caption font-medium text-ink shadow-card">{t('p7.disclaimer')}</div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button size="sm" variant="secondary" icon={LocateFixed} onClick={fly} disabled={!place}>{place ? t('p7.fly') : t('p7.noPlace')}</Button>
        <label className="flex min-h-11 items-center gap-2 text-body-sm text-ink">
          <input type="checkbox" checked={orbit && !reduced} disabled={reduced} onChange={(e) => setOrbit(e.target.checked)} className="size-4 accent-[var(--brand)]" />{t('p7.orbit')}
        </label>
      </div>
      <p className="text-caption text-muted">{noExtent ? t('p7.noExtent') : t('p7.extentNote')}</p>
    </div>
  )
}
