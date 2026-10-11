import { useState } from 'react'
import { AlertTriangle, Zap } from 'lucide-react'
import { api } from '../../api'
import { useApp } from '../../ctx'
import { usePlace, zipOf } from '../../state/place'
import { Card, Checkbox, Freshness, SkeletonText, SourceLink } from '../ds'
import { useAsync } from '../ui'

const PUC = 'https://www.ercot.com/files/docs/2024/01/17/PUC-Critical-Care-Form.pdf'
const CDC = 'https://www.cdc.gov/carbon-monoxide/about/index.html'
const EMPOWER_SRC = 'https://catalog.data.gov/dataset/hhs_empower_rest_service_public'
const KEY = 'floodready.powerSteps.v1'

function load(): boolean[] {
  try { const v = JSON.parse(localStorage.getItem(KEY) ?? '[]'); if (Array.isArray(v)) return [0, 1, 2, 3].map((i) => !!v[i]) } catch { /* ignore */ }
  return [false, false, false, false]
}

/** Power-dependent medical device checklist. ZIP count is optional; static steps always show. */
export default function PowerDependentCard() {
  const { t, lang } = useApp()
  const { place } = usePlace()
  const zip = place?.zip ?? zipOf(place?.label) ?? null
  const [done, setDone] = useState<boolean[]>(load)
  const e = useAsync(() => api.empower(zip!), [zip], !!zip)
  const d = e.data
  const n = d?.available ? d.power_dependent_devices : null
  const toggle = (i: number, v: boolean) => {
    const next = done.map((x, j) => (j === i ? v : x)); setDone(next)
    try { localStorage.setItem(KEY, JSON.stringify(next)) } catch { /* ignore */ }
  }
  const links = [
    { href: PUC, label: t('pw.puc') }, { href: 'https://tdem.texas.gov/stear', label: t('pw.stear') },
  ]
  return (
    <Card title={t('pw.h')} subtitle={t('pw.sub')} titleAs="h2" id="prepare-power">
      {zip && e.loading && <div aria-busy="true"><SkeletonText lines={2} /></div>}
      {zip && !e.loading && typeof n === 'number' && d && (
        <div className="mb-3 rounded-lg bg-surface-2 p-3 text-body-sm text-ink">
          <p>{t('pw.zip').replace('{zip}', d.zip).replace('{n}', n.toLocaleString(lang))}</p>
          <p className="mt-1 text-caption text-muted">{t('pw.zipNote')}</p>
          <p className="mt-1 flex flex-wrap items-center gap-2"><SourceLink href={d.source || EMPOWER_SRC} /><a className="text-caption font-semibold text-brand underline" href={d.map || 'https://empowerprogram.hhs.gov/empowermap'} target="_blank" rel="noreferrer">{t('pw.map')}</a><Freshness meta={d.meta} /></p>
        </div>
      )}
      {zip && !e.loading && typeof n !== 'number' && <p className="mb-3 text-body-sm text-muted">{t('pw.fallback')}</p>}
      <ul>
        {[0, 1, 2, 3].map((i) => (
          <li key={i}><Checkbox label={<span><Zap aria-hidden size={14} className="mr-1 inline" />{t('pw.s' + (i + 1))}</span>} checked={done[i]} onChange={(v) => toggle(i, v)} /></li>
        ))}
      </ul>
      <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1">{links.map((l) => <SourceLink key={l.href} href={l.href} label={l.label} />)}</p>
      <p className="mt-3 text-body-sm font-semibold text-ink">{t('pw.honest')}</p>
      <div role="alert" className="mt-3 rounded-lg border border-danger/40 bg-danger/10 p-3 text-body-sm text-ink">
        <p><AlertTriangle aria-hidden size={16} className="mr-1 inline text-danger" />{t('pw.co')}</p>
        <p className="mt-1"><SourceLink href={CDC} label={t('pw.coSrc')} /></p>
      </div>
    </Card>
  )
}
