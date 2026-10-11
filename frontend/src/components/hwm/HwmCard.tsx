import { useEffect, useState } from 'react'
import { apiC20, type Hwm } from '../../api'
import { useApp } from '../../ctx'
import { Freshness, SourceLink } from '../ds'

export function useHwm(loc: { lat: number; lon: number } | null) {
  const [d, setD] = useState<Hwm | null>(null)
  useEffect(() => {
    setD(null)
    if (!loc) return
    let live = true
    apiC20.hwm(loc).then((e) => { if (live) setD(e) })
    return () => { live = false }
  }, [loc?.lat, loc?.lon]) // eslint-disable-line react-hooks/exhaustive-deps
  return d
}

export const hasMarks = (d: Hwm | null): d is Hwm => !!d && Array.isArray(d.marks) && d.marks.length > 0

export default function HwmBody({ d }: { d: Hwm }) {
  const { t } = useApp()
  const marks = d.marks.slice(0, 3)
  return (
    <div className="space-y-3 text-body-sm text-ink">
      <ul className="divide-y divide-line rounded-md border border-line">
        {marks.map((m) => (
          <li key={m.id} className="px-3 py-2">
            <p className="font-semibold">
              {m.height_above_ground_ft == null ? t('p10.hwm.noDepth')
                : m.height_above_ground_ft === 0 ? t('p10.hwm.zero')
                : t('p10.hwm.depth').replace('{ft}', String(m.height_above_ground_ft))}
              <span className="font-normal text-muted"> · {t('p10.hwm.dist').replace('{mi}', m.distance_mi.toFixed(1))}</span>
            </p>
            {m.site_desc && <p className="text-caption text-muted">{m.site_desc}</p>}
            {m.url && <SourceLink href={m.url} />}
          </li>
        ))}
      </ul>
      <p className="text-caption text-muted">{t('p10.hwm.note')}</p>
      <div className="flex flex-wrap items-center gap-3"><Freshness meta={d.meta} />{d.source && /^https?:/.test(d.source) && <SourceLink href={d.source} />}</div>
    </div>
  )
}
