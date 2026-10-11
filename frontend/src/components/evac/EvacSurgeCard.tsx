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

/** Body of the Home "Evacuation zone and storm surge" disclosure. */
export default function EvacSurgeBody({ d }: { d: Evac }) {
  const { t } = useApp()
  const cats = [1, 2, 3, 4, 5].map((n) => [n, d.surge?.['cat' + n] ?? null] as const)
  const anySurge = cats.some(([, v]) => v)
  return (
    <div className="space-y-3 text-body-sm text-ink">
      <p className="font-semibold">{d.zone ? (d.zone_label || `${t('p10.zone')} ${d.zone}`) : t('p10.noZone')}</p>
      {d.surge && (anySurge ? (
        <ul className="divide-y divide-line rounded-md border border-line">
          {cats.map(([n, v]) => <li key={n} className="flex justify-between gap-3 px-3 py-2"><span>{t('p10.cat')} {n}</span><span className="text-muted">{v ?? t('p10.noSurge')}</span></li>)}
        </ul>
      ) : <p>{t('p10.surgeNone')}</p>)}
      <p className="text-caption text-muted">{t('p10.evac.note')}</p>
      <div className="flex flex-wrap items-center gap-3"><Freshness meta={d.meta} /><SourceLink href="https://www.readyharris.org/" /></div>
    </div>
  )
}
