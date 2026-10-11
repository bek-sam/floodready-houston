import { api } from '../api'
import { useApp } from '../ctx'
import { fill } from '../lib/summary'
import { Skeleton } from './ds'
import { useAsync } from './ui'

/** 48h stage sparkline for one gauge. Fixed size (no layout shift). Errors/404 show a quiet dash. */
export default function Sparkline({ id, width = 96, height = 32 }: { id: string; width?: number; height?: number }) {
  const { t } = useApp()
  const h = useAsync(() => api.gaugeHistory(id, 48), [id])
  const pts = (Array.isArray(h.data?.readings) ? h.data!.readings : []).map((r) => ({ x: Date.parse(r.t), y: r.stage_ft })).filter((p) => !isNaN(p.x) && typeof p.y === 'number')
  const box = { width, height }
  if (h.loading) return <span className="block shrink-0" style={box}><Skeleton w={width} h={height} radius={6} /></span>
  if (h.error || pts.length < 2) {
    return (
      <span className="flex shrink-0 items-center justify-center text-caption text-muted" style={box}>
        <span aria-hidden>—</span><span className="sr-only">{t('spark.none')}</span>
      </span>
    )
  }
  const W = width, H = height, P = 4
  const x0 = pts[0].x, x1 = pts[pts.length - 1].x
  const ys = pts.map((p) => p.y), lo = Math.min(...ys), hi = Math.max(...ys)
  const sx = (x: number) => P + ((x - x0) / (x1 - x0 || 1)) * (W - 2 * P)
  const sy = (y: number) => H - P - ((y - lo) / (hi - lo || 1)) * (H - 2 * P)
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join('')
  const first = pts[0], last = pts[pts.length - 1]
  // Trend over 48h: more than 0.5 ft change counts as rising/falling.
  const diff = last.y - first.y
  const trend = diff > 0.5 ? 'rising' : diff < -0.5 ? 'falling' : 'steady'
  const label = fill(t, 'spark.label', { trend: '@spark.' + trend, now: last.y.toFixed(1) })
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} className="block shrink-0">
      <title>{label}</title>
      <path d={d} fill="none" stroke="var(--water)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={sx(last.x)} cy={sy(last.y)} r={3.5} fill="var(--water)" stroke="var(--surface)" strokeWidth={2} />
    </svg>
  )
}
