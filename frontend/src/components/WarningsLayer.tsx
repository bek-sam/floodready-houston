import { useEffect, useState } from 'react'
import { GeoJSON } from 'react-leaflet'
import type { Feature, Geometry } from 'geojson'
import { api, type AreaAlerts, type LatLon } from '../api'
import { useApp } from '../ctx'
import { Freshness, Switch } from './ds'

/** Zone-only warnings are shown only for the Houston region (drops e.g. Corpus Christi). */
const HOUSTON_REGION = /Harris|Fort Bend|Montgomery|Galveston|Brazoria|Chambers|Liberty|Waller/i

const color = (event: string) => (/flash flood warning/i.test(event) ? '#C62828' : /warning/i.test(event) ? '#EF6C00' : '#F9A825')

/** GET /alerts/area around a point (about 1 degree each way). Failures give null. */
export function useAreaAlerts(loc: LatLon | null | undefined) {
  const [d, setD] = useState<AreaAlerts | null>(null)
  const k = loc ? `${loc.lat.toFixed(2)},${loc.lon.toFixed(2)}` : ''
  useEffect(() => {
    if (!loc) return
    let live = true
    const bbox = [loc.lon - 1, loc.lat - 1, loc.lon + 1, loc.lat + 1].map((n) => n.toFixed(3)).join(',')
    api.alertsArea(bbox).then((r) => { if (live) setD(r) }).catch(() => { if (live) setD(null) })
    return () => { live = false }
  }, [k]) // eslint-disable-line react-hooks/exhaustive-deps
  return d
}

const withGeom = (d: AreaAlerts | null) => (Array.isArray(d?.features) ? d!.features : []).filter((f) => f && f.geometry && f.properties)

/** Leaflet layer; render inside <Map>. Features without geometry never reach Leaflet. */
export function WarningsMapLayer({ data, on }: { data: AreaAlerts | null; on: boolean }) {
  const { t } = useApp()
  const feats = withGeom(data)
  if (!on || !feats.length) return null
  return (
    <GeoJSON key={feats.map((f) => f.properties.id).join('|')} data={{ type: 'FeatureCollection', features: feats } as never}
      style={(f) => ({ color: color(f?.properties?.event ?? ''), weight: 2, fillOpacity: 0.25 })}
      onEachFeature={(f: Feature<Geometry, { event?: string; headline?: string; expires?: string; source?: string }>, layer) => {
        const p = f.properties ?? {}
        const el = document.createElement('div')
        const b = document.createElement('b'); b.textContent = p.event ?? ''; el.append(b)
        if (p.headline) { const h = document.createElement('div'); h.textContent = p.headline; el.append(h) }
        if (p.expires) { const e = document.createElement('div'); e.textContent = `${t('p32.warn.expires')}: ${new Date(p.expires).toLocaleString()}`; el.append(e) }
        if (p.source && /^https:\/\//.test(p.source)) { const a = document.createElement('a'); a.href = p.source; a.target = '_blank'; a.rel = 'noreferrer'; a.textContent = 'api.weather.gov'; el.append(a) }
        layer.bindPopup(el)
      }} />
  )
}

/** Toggle + zone-only chips + empty state + freshness. Render above the map. */
export function WarningsBar({ data, on, onChange }: { data: AreaAlerts | null; on: boolean; onChange: (v: boolean) => void }) {
  const { t } = useApp()
  if (!data) return null
  const zones = (Array.isArray(data.zone_only) ? data.zone_only : []).filter((z) => HOUSTON_REGION.test(z.area_desc ?? ''))
  const n = withGeom(data).length
  return (
    <div className="mb-2 space-y-1">
      <Switch label={t('p32.warn.toggle')} checked={on} onChange={onChange} />
      {zones.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label={t('p32.warn.zoneOnly')}>
          {zones.slice(0, 6).map((z, i) => (
            <li key={i} title={z.headline} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-caption text-ink">
              {z.event}{z.area_desc ? ` · ${z.area_desc.slice(0, 50)}` : ''}
            </li>
          ))}
        </ul>
      )}
      {zones.length > 0 && <p className="text-caption text-muted">{t('p32.warn.zoneNote')}</p>}
      {n === 0 && zones.length === 0 && <p className="text-caption text-muted">{t('p32.warn.none')}</p>}
      <Freshness meta={data.meta} />
    </div>
  )
}

/** State helper: default ON once any polygon is returned. */
export function useWarningsOn(data: AreaAlerts | null): [boolean, (v: boolean) => void] {
  const [v, setV] = useState<boolean | null>(null)
  return [v ?? withGeom(data).length > 0, setV]
}
