import { useEffect, useState } from 'react'
import { Waves } from 'lucide-react'
import { apiC20, type Coastal } from '../../api'
import { useApp } from '../../ctx'
import { Freshness } from '../ds'

/** Galveston tide anomaly + active NHC storms. Renders nothing when /coastal has no data. */
export default function CoastalChip() {
  const { t } = useApp()
  const [d, setD] = useState<Coastal | null>(null)
  useEffect(() => { let live = true; apiC20.coastal().then((c) => { if (live) setD(c) }); return () => { live = false } }, [])
  const a = d?.tide?.anomaly_ft
  const storms = (d?.active_storms ?? []).filter((s) => s && s.name && s.relevant !== false && s.gulf_of_mexico !== false)
  if (!d || (a == null && !storms.length)) return null
  const txt = a == null ? t('p10.tide.unavail')
    : t('p10.tide').replace('{ft}', (a >= 0 ? '+' : '') + a.toFixed(1))
  return (
    <div className="mt-3 space-y-1 rounded-lg border border-line bg-surface px-3 py-2 text-body-sm text-ink">
      <p className="flex flex-wrap items-center gap-2"><Waves aria-hidden size={16} className="text-water" /><span className="font-semibold">{txt}</span><Freshness meta={d.meta} /></p>
      {storms.map((s) => (
        <p key={s.name} className="text-caption text-muted">
          {t('p10.storm').replace('{name}', s.name).replace('{type}', s.type || '')}
          {s.advisory_url && /^https?:/.test(s.advisory_url) && <> · <a className="text-brand underline" href={s.advisory_url} target="_blank" rel="noreferrer">{t('p10.nhc')}</a></>}
        </p>
      ))}
    </div>
  )
}
