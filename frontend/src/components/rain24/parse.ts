// Parser for /api/rain24. Returns null when unavailable or unusable, never zeros.
export interface RainWindow { start: number; end: number; inches: number }
export interface PopPoint { t: number; pct: number }
export interface Rain24 {
  windows: RainWindow[]; pop: PopPoint[]; asOf: string | null; source: string | null; sourceUrl: string | null
  action: { show: boolean; text: string; windowStart: number | null } | null
}

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const ms = (v: unknown): number | null => { if (typeof v === 'string') { const d = Date.parse(v); return Number.isNaN(d) ? null : d } return num(v) }
const rec = (v: unknown): Record<string, unknown> | null => (v && typeof v === 'object' ? (v as Record<string, unknown>) : null)

export function parseRain24(raw: unknown): Rain24 | null {
  const o = rec(raw)
  if (!o || o.available !== true || num(o.total_inches) == null) return null
  const windows: RainWindow[] = []
  for (const x of Array.isArray(o.windows) ? o.windows : []) {
    const w = rec(x); if (!w) continue
    const start = ms(w.start), inches = num(w.inches)
    if (start == null || inches == null) continue
    windows.push({ start, end: ms(w.end) ?? start + 6 * 3600e3, inches: Math.max(0, inches) })
  }
  const pop: PopPoint[] = []
  for (const x of Array.isArray(o.pop_hourly) ? o.pop_hourly : []) {
    const p = rec(x); if (!p) continue
    const t = ms(p.start), pct = num(p.pop_pct)
    if (t != null && pct != null) pop.push({ t, pct: Math.min(100, Math.max(0, pct)) })
  }
  if (!windows.length && !pop.length) return null
  const a = rec(o.action), meta = rec(o.meta)
  return {
    windows: windows.slice(0, 4), pop: pop.slice(0, 24),
    asOf: typeof meta?.as_of === 'string' ? meta.as_of : null,
    source: typeof o.source === 'string' ? o.source : null,
    sourceUrl: typeof o.source_url === 'string' && /^https:\/\//.test(o.source_url) ? o.source_url : null,
    action: a && typeof a.text === 'string' ? { show: a.show === true, text: a.text, windowStart: ms(a.window_start) } : null,
  }
}
