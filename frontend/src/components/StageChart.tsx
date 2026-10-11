import { useMemo, useState } from 'react'
import type { ReplayGauge } from '../api'
import { useApp } from '../ctx'

// viewBox is ~480 wide so it scales ~0.7x at 375px: 17 units renders as >=12px text
const W = 480, H = 280, L = 36, R = 116, T = 18, B = 34, FS = 17, LH = 20

const THRESH = [
  ['major', 'Major'], ['moderate', 'Moderate'], ['minor', 'Minor'], ['action', 'Action'],
] as const

/** Single-series line (stage) with labeled flood-stage reference lines, hover crosshair, and a table view. */
export default function StageChart({ gauge, cursor }: { gauge: ReplayGauge; cursor: number }) {
  const { t } = useApp()
  const [hover, setHover] = useState<number | null>(null)
  const [table, setTable] = useState(false)

  const pts = useMemo(() => (gauge.series ?? []).map((p) => ({ x: Date.parse(p.t), y: p.stage_ft })).filter((p) => !isNaN(p.x) && typeof p.y === 'number'), [gauge])
  if (pts.length < 2) return <p className="text-body-sm text-muted">{t('p5.replay.nodata')}</p>

  const x0 = pts[0].x, x1 = pts[pts.length - 1].x
  const fs = gauge.flood_stages ?? { action: null, minor: null, moderate: null, major: null }
  const yMaxData = Math.max(...pts.map((p) => p.y))
  const firstThresh = fs.moderate ?? fs.minor ?? fs.action ?? 0
  const yMax = Math.max(yMaxData, firstThresh) * 1.08 || 1
  const yMinData = Math.min(...pts.map((p) => p.y))
  const lowThresh = Math.min(...[fs.action, fs.minor, fs.moderate, fs.major].filter((v): v is number => v != null), yMinData)
  // start just below the lowest threshold/value instead of 0 so the thresholds are not squashed together
  const yMin = Math.max(0, Math.floor(lowThresh - (yMax - lowThresh) * 0.1))
  const sx = (x: number) => L + ((x - x0) / (x1 - x0 || 1)) * (W - L - R)
  const sy = (y: number) => T + (1 - (y - yMin) / (yMax - yMin || 1)) * (H - T - B)
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join('')
  const ticks = [0, 1, 2, 3, 4].map((i) => yMin + ((yMax - yMin) * i) / 4)
  const xt = [0, 0.5, 1].map((f) => x0 + (x1 - x0) * f)
  const fmtD = (ms: number) => new Date(ms).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  const fmtDT = (ms: number) => new Date(ms).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric' })

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * W
    const tx = x0 + ((px - L) / (W - L - R)) * (x1 - x0)
    let best = 0, bd = Infinity
    pts.forEach((p, i) => { const d = Math.abs(p.x - tx); if (d < bd) { bd = d; best = i } })
    setHover(best)
  }
  // label y positions: keep >=LH apart, clamped above the x-axis (top to bottom) so close thresholds stay readable
  const lyRef: Record<string, number> = {}
  let lastY = -Infinity
  THRESH.map(([k]) => [k, fs[k]] as const).filter(([, v]) => v != null && v <= yMax)
    .sort((p, q2) => sy(p[1]!) - sy(q2[1]!)).forEach(([k, v]) => { lastY = Math.min(Math.max(sy(v!) + 5, lastY + LH), H - B - 2); lyRef[k] = lastY })
  const hp = hover != null ? pts[hover] : null
  const cx = Math.min(Math.max(cursor, x0), x1)

  return (
    <figure className="m-0">
      <figcaption className="mb-1 flex items-center justify-between gap-2 text-sm">
        <span className="font-semibold">{t('replay.chart')}: {gauge.name}</span>
        <button type="button" aria-pressed={table} className="min-h-11 text-brand underline" onClick={() => setTable(!table)}>
          {table ? t('replay.viewChart') : t('replay.viewTable')}
        </button>
      </figcaption>
      {table ? (
        <div className="max-h-64 overflow-auto rounded-lg border border-line">
          <table className="w-full text-sm">
            <caption className="sr-only">{t('replay.chart')}: {gauge.name}</caption><thead className="sticky top-0 bg-surface"><tr><th scope="col" className="p-2 text-start">Time</th><th scope="col" className="p-2 text-end">Stage (ft)</th></tr></thead>
            <tbody>{pts.filter((_, i) => i % Math.ceil(pts.length / 80) === 0).map((p) => (
              <tr key={p.x} className="border-t border-line"><td className="p-2">{fmtDT(p.x)}</td><td className="p-2 text-end">{p.y.toFixed(2)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full touch-pan-y overflow-visible" role="img"
          aria-label={`Stage in feet over time at ${gauge.name}, peak ${yMaxData.toFixed(1)} ft. Use the table view for all values.`}
          onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
          {ticks.map((v) => (
            <g key={v}>
              <line x1={L} x2={W - R} y1={sy(v)} y2={sy(v)} stroke="var(--c-grid)" strokeWidth="1" />
              <text x={L - 5} y={sy(v) + 6} textAnchor="end" fontSize={FS} fill="var(--muted)">{v.toFixed(0)}</text>
            </g>
          ))}
          {xt.map((v, i) => (
            <text key={i} x={sx(v)} y={H - 9} textAnchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'} fontSize={FS} fill="var(--muted)">{fmtD(v)}</text>
          ))}
          <text x={L + 4} y={T - 4} fontSize={FS} fill="var(--muted)">ft</text>
          {THRESH.map(([k, label]) => {
            const v = fs[k]
            if (v == null || v > yMax) return null
            return (
              <g key={k}>
                <line x1={L} x2={W - R} y1={sy(v)} y2={sy(v)} stroke={`var(--s-${k})`} strokeWidth="1.5" strokeDasharray="5 4" />
                <text x={W - R + 4} y={lyRef[k] ?? sy(v) + 5} fontSize={FS} fill="var(--ink)">{label} {v}</text>
              </g>
            )
          })}
          <line x1={sx(cx)} x2={sx(cx)} y1={T} y2={H - B} stroke="var(--muted)" strokeWidth="1" strokeDasharray="2 3" />
          <path d={path} fill="none" stroke="var(--c-line)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
          {hp && (
            <g pointerEvents="none">
              <line x1={sx(hp.x)} x2={sx(hp.x)} y1={T} y2={H - B} stroke="var(--ink)" strokeWidth="1" />
              <circle cx={sx(hp.x)} cy={sy(hp.y)} r="5" fill="var(--c-line)" stroke="var(--surface)" strokeWidth="2" />
              <g transform={`translate(${Math.min(sx(hp.x) + 8, W - R - 130)},${T + 6})`}>
                <rect width="130" height="44" rx="6" fill="var(--surface)" stroke="var(--line)" />
                <text x="8" y="18" fontSize={FS} fill="var(--muted)">{fmtDT(hp.x)}</text>
                <text x="8" y="37" fontSize={FS} fontWeight="600" fill="var(--ink)">{hp.y.toFixed(2)} ft</text>
              </g>
            </g>
          )}
        </svg>
      )}
    </figure>
  )
}
