import { useEffect, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { useApp } from '../../ctx'
import type { SummaryInputs } from '../../lib/summary'

interface Snap { at: number; alerts: string[]; gauges: Record<string, { n: string; s: string }>; outlook: string | null; evac: string | null }
const KEY = 'floodready.digest.v1'
const ORDER = ['normal', 'action', 'minor', 'moderate', 'major']
const OUT = ['None', 'Marginal', 'Slight', 'Moderate', 'High']

function snapOf(i: SummaryInputs): Snap | null {
  // Only snapshot when every source resolved; a partial snapshot would fake "changes".
  if (!i.risk.data || !i.alerts.data || !i.outlook.data || i.risk.failed || i.alerts.failed || i.outlook.failed) return null
  const gauges: Snap['gauges'] = {}
  for (const g of i.risk.data.nearest_gauges ?? []) if (g?.id) gauges[g.id] = { n: g.name, s: g.status }
  return {
    at: Date.now(),
    alerts: (i.alerts.data.alerts ?? []).map((a) => a?.event).filter(Boolean).sort(),
    gauges, outlook: i.outlook.data.day1?.category ?? null, evac: i.evac?.zone_status ?? null,
  }
}
type Ch = { key: string; vars?: Record<string, string> }
function diff(a: Snap, b: Snap): Ch[] {
  const out: Ch[] = []
  const added = b.alerts.filter((e) => !a.alerts.includes(e))
  if (added.length) out.push({ key: 'p11b.dg.alertNew', vars: { event: added[0] } })
  if (a.alerts.some((e) => !b.alerts.includes(e)) && !b.alerts.length) out.push({ key: 'p11b.dg.alertGone' })
  for (const id of Object.keys(b.gauges)) {
    const p = a.gauges[id], c = b.gauges[id]
    if (!p || p.s === c.s || ORDER.indexOf(p.s) < 0 || ORDER.indexOf(c.s) < 0) continue
    out.push({ key: ORDER.indexOf(c.s) > ORDER.indexOf(p.s) ? 'p11b.dg.rose' : 'p11b.dg.fell', vars: { gauge: c.n, from: '@gauge.' + p.s, to: '@gauge.' + c.s } })
  }
  if (a.outlook && b.outlook && a.outlook !== b.outlook && OUT.includes(a.outlook) && OUT.includes(b.outlook)) out.push({ key: 'p11b.dg.outlook', vars: { cat: '@sum.cat.' + b.outlook } })
  if (a.evac && b.evac && a.evac !== b.evac && a.evac !== 'unavailable' && b.evac !== 'unavailable') out.push({ key: 'p11b.dg.evac' })
  return out.slice(0, 4)
}

export default function DigestBanner({ inputs, placeKey }: { inputs: SummaryInputs; placeKey: string }) {
  const { t } = useApp()
  const prev = useRef<{ k: string; s: Snap | null } | null>(null)
  const [changes, setChanges] = useState<Ch[]>([])
  const [since, setSince] = useState(0)
  const [hidden, setHidden] = useState(false)
  const cur = snapOf(inputs)
  const sig = cur ? JSON.stringify({ ...cur, at: 0 }) : ''
  useEffect(() => {
    if (!cur) return
    try {
      const all = JSON.parse(localStorage.getItem(KEY) || '{}') as Record<string, Snap>
      if (!prev.current || prev.current.k !== placeKey) { // first complete load this visit: compare with the stored snapshot
        const old = all[placeKey] ?? null
        prev.current = { k: placeKey, s: old }
        if (old) { setChanges(diff(old, cur)); setSince(old.at); setHidden(false) }
      }
      all[placeKey] = cur
      localStorage.setItem(KEY, JSON.stringify(all))
    } catch { /* storage unavailable: no digest */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig, placeKey])
  if (hidden || !changes.length) return null
  const tv = (s: string) => (s.startsWith('@') ? t(s.slice(1)) : s)
  const line = (c: Ch) => Object.entries(c.vars ?? {}).reduce((s, [k, v]) => s.replace(`{${k}}`, tv(v)), t(c.key))
  return (
    <section role="status" aria-label={t('p11b.dg.title')} className="rounded-lg border border-line bg-surface-2 p-3 text-body-sm">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ink">{t('p11b.dg.title')} <span className="font-normal text-muted">({new Date(since).toLocaleString()})</span></p>
          <ul className="mt-1 list-disc ps-5 text-ink">{changes.map((c, i) => <li key={i}>{line(c)}</li>)}</ul>
        </div>
        <button type="button" onClick={() => setHidden(true)} aria-label={t('p11b.dg.dismiss')} className="grid min-h-11 min-w-11 place-items-center text-muted"><X aria-hidden size={18} /></button>
      </div>
    </section>
  )
}
