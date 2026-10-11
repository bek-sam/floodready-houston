import { useId } from 'react'
import type { FloodStages, Status } from '../api'
import { statusColor } from './ui'
import { gaugeLabelKey } from '../lib/levels'
import { useApp } from '../ctx'

const LEVELS = [['major', 'Major'], ['moderate', 'Moderate'], ['minor', 'Minor'], ['action', 'Action']] as const

/** Vertical gauge "tube": water fills past labeled action/minor/moderate/major lines. One value, fill colored by current status. */
export default function WaterTube({ stage, stages, status, title, unit = 'ft' }: {
  stage: number | null; stages: FloodStages; status: Status; title: string; unit?: string
}) {
  const clipId = useId()
  const { t } = useApp()
  const marks: { k: Status; l: string; v: number }[] = []
  LEVELS.forEach(([k, l]) => { const v = stages?.[k]; if (v != null) marks.push({ k, l, v }) })
  const top = Math.max(stage ?? 0, ...marks.map((m) => m.v), 1) * 1.1
  const H = 240, TOP = 14, BOT = 14, X = 8, TW = 56, FS = 17, LH = 20
  const y = (v: number) => TOP + (1 - Math.max(0, v) / top) * (H - TOP - BOT)
  const fy = stage != null ? y(stage) : H - BOT
  const col = statusColor(status)
  // labels at least LH apart (top to bottom), clamped inside the tube's height
  const ly: Record<string, number> = {}
  let last = -Infinity
  ;[...marks].sort((a, b) => y(a.v) - y(b.v)).forEach((m) => { last = Math.min(Math.max(y(m.v) + 6, last + LH), H - BOT - LH); ly[m.k] = last })
  return (
    <svg viewBox={`0 0 280 ${H + 4}`} className="mx-auto w-full max-w-xs" role="img"
      aria-label={`${title}: ${stage != null ? stage.toFixed(1) + ' ' + unit : '—'}, ${t(gaugeLabelKey(status))}`}>
      <rect x={X} y={TOP} width={TW} height={H - TOP - BOT} rx={10} fill="var(--surface-2)" stroke="var(--line)" strokeWidth={2} />
      {stage != null && (
        <>
          <clipPath id={clipId}><rect x={X} y={TOP} width={TW} height={H - TOP - BOT} rx={10} /></clipPath>
          <rect x={X} y={fy} width={TW} height={H - BOT - fy} fill={col} clipPath={`url(#${clipId})`} style={{ transition: 'y 0.15s, height 0.15s' }} />
        </>
      )}
      {marks.map((m) => (
        <g key={m.k}>
          <line x1={X - 4} x2={X + TW + 8} y1={y(m.v)} y2={y(m.v)} stroke={statusColor(m.k)} strokeWidth={2} strokeDasharray="4 3" />
          <line x1={X + TW + 8} x2={X + TW + 12} y1={y(m.v)} y2={ly[m.k] - 6} stroke={statusColor(m.k)} strokeWidth={1} />
          <text x={X + TW + 14} y={ly[m.k]} fontSize={FS} fill="var(--ink)">{m.l} {m.v} {unit}</text>
        </g>
      ))}
      <text x={X + TW + 14} y={H - BOT + 2} fontSize={FS} fill="var(--muted)">0</text>
      {stage != null && (
        <text x={X + TW / 2} y={Math.min(fy - 4, H - BOT - 6) < TOP + 12 ? TOP + 12 : Math.min(fy - 4, H - BOT - 6)} textAnchor="middle" fontSize={FS} fontWeight={700} fill="var(--ink)">{stage.toFixed(1)}</text>
      )}
    </svg>
  )
}
