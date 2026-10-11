import { useEffect, useState } from 'react'
import { apiC20, type Evac } from '../../api'
import { useApp } from '../../ctx'
import { Freshness, SourceLink } from '../ds'

export function useEvac(loc: { lat: number; lon: number } | null) {
  const [d, setD] = useState<Evac | null>(null)
  useEffect(() => {
    setD(null)
    if (!loc) return
    let live = true
    apiC20.evac(loc).then((e) => { if (live) setD(e) })
    return () => { live = false }
  }, [loc?.lat, loc?.lon]) // eslint-disable-line react-hooks/exhaustive-deps
  return d
}

export type ZoneState = 'in' | 'out' | 'unavailable'
/** Never treat a failed lookup as "not in a zone". */
export function zoneState(d: Evac): ZoneState {
  if (d.zone_status === 'unavailable') return 'unavailable'
  if (d.zone) return 'in'
  if (d.zone_status === 'in_zone') return 'in'
  return 'out'
}
export const surgeText = (v: unknown): string | null => {
  if (!v) return null
  if (typeof v === 'object') { const o = v as { label?: string; min_ft?: number | null; max_ft?: number | null }
    return o.label || (o.max_ft == null ? (o.min_ft != null ? `${o.min_ft}+ ft` : null) : `${o.min_ft ?? 0}-${o.max_ft} ft`) }
  return String(v)
}
/** Home disclosure should render only when there is something real to say. */
export const evacShow = (d: Evac | null | undefined): boolean => !!d && (zoneState(d) !== 'out' || d.zone_status === 'not_in_zone' || !!d.surge && Object.values(d.surge).some(Boolean))

/** Body of the Home "Evacuation zone and storm surge" disclosure. */
export default function EvacSurgeBody({ d }: { d: Evac }) {
  const { t } = useApp()
  const zs = zoneState(d)
  const unavailable = zs === 'unavailable' || d.surge_status === 'unavailable'
  const cats = [1, 2, 3, 4, 5].map((n) => [n, surgeText(d.surge?.['cat' + n])] as const)
  const anySurge = cats.some(([, v]) => v)
  return (
    <div className="space-y-3 text-body-sm text-ink">
      <p className="font-semibold">{zs === 'unavailable' ? t('p10.zoneUnavail') : zs === 'in' ? (d.zone_label || `${t('p10.zone')} ${d.zone ?? ''}`) : t('p10.noZone')}</p>
      {unavailable && <p>{t('p10.surgeUnavail')}</p>}
      {!unavailable && d.surge && (anySurge ? (
        <ul className="divide-y divide-line rounded-md border border-line">
          {cats.map(([n, v]) => <li key={n} className="flex justify-between gap-3 px-3 py-2"><span>{t('p10.cat')} {n}</span><span className="text-muted">{v ?? t('p10.noSurge')}</span></li>)}
        </ul>
      ) : <p>{t('p10.surgeNone')}</p>)}
      <p className="text-caption text-muted">{t('p10.evac.note')}</p>
      <div className="flex flex-wrap items-center gap-3"><Freshness meta={d.meta} /><SourceLink href="https://www.readyharris.org/" /></div>
    </div>
  )
}
