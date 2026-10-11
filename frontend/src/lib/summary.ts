// Home readiness summary rules (docs/ux/redesign-spec.md §4.3, §4.4). Pure functions, no React.
// Inputs come only from /risk, /flood-history, /zip-insurance, /alerts and /outlook.
import type { Alert, Alerts, FloodHistory, Gauge, Outlook, Risk, Status, ZipInsurance } from '../api'
import type { Household } from '../state/place'
import { gaugeLevel, LEVEL_RANK, type Exposure, type Level } from './levels'

/** One endpoint's state. `done` = resolved (data or failure). */
export interface Src<T> { data: T | null; failed: boolean; done: boolean }
export interface SummaryInputs {
  risk: Src<Risk>; alerts: Src<Alerts>; outlook: Src<Outlook>; hist: Src<FloodHistory>
  /** null when the place has no ZIP. */
  zip: Src<ZipInsurance> | null
}
/** i18n key + placeholder values (values may themselves be i18n keys when prefixed with "@"). */
export interface Reason { key: string; vars?: Record<string, string> }

export const isFloodAlert = (event: string | null | undefined) => /flood|hurricane|tropical|storm surge|coastal/i.test(event ?? '')
/** Badge level for one NWS alert event name. */
export const alertLevel = (event: string): Level =>
  /flash flood emergency/i.test(event) ? 'danger' : /warning/i.test(event) ? 'warning' : 'watch'

const gaugesOf = (r: Risk | null): Gauge[] => (Array.isArray(r?.nearest_gauges) ? r!.nearest_gauges : []).filter((g) => g && g.id)
const alertsOf = (a: Alerts | null): Alert[] => (Array.isArray(a?.alerts) ? a!.alerts : []).filter((x) => x && typeof x.event === 'string')

// ---------- A. Right now ----------
export interface RightNow { level: Level; final: boolean; reason: Reason; dangerEvent?: string }

export function rightNow(i: SummaryInputs): RightNow {
  const { risk, alerts, outlook } = i
  if (!risk.done || !alerts.done || !outlook.done) return { level: 'unknown', final: false, reason: { key: 'sum.checking' } }
  if (risk.failed && alerts.failed) return { level: 'unknown', final: true, reason: { key: 'sum.now.unknown' } }
  const al = alertsOf(alerts.data)
  const flood = al.filter((a) => isFloodAlert(a.event))
  const gauges = gaugesOf(risk.data)
  const ev = (a: Alert) => ({ key: 'sum.now.event', vars: { event: a.event } })

  const emergency = al.find((a) => /flash flood emergency/i.test(a.event))
  if (emergency) return { level: 'danger', final: true, reason: ev(emergency), dangerEvent: emergency.event }
  const major = gauges.find((g) => g.status === 'major')
  if (major) return { level: 'danger', final: true, reason: { key: 'sum.now.gaugeMajor', vars: { gauge: major.name } }, dangerEvent: major.name }

  const warn = flood.find((a) => /warning/i.test(a.event))
  if (warn) return { level: 'warning', final: true, reason: ev(warn) }
  const flooding = gauges.find((g) => g.status === 'moderate' || g.status === 'minor')
  if (flooding) return { level: 'warning', final: true, reason: { key: 'sum.now.gaugeFlood', vars: { gauge: flooding.name, status: '@gauge.' + flooding.status } } }

  if (flood[0]) return { level: 'watch', final: true, reason: ev(flood[0]) }
  const near = gauges.find((g) => g.status === 'action')
  if (near) return { level: 'watch', final: true, reason: { key: 'sum.now.gaugeNear', vars: { gauge: near.name } } }
  const cat = outlook.data?.day1?.category
  if (cat === 'Moderate' || cat === 'High') return { level: 'watch', final: true, reason: { key: 'sum.now.outlook', vars: { category: '@sum.cat.' + cat } } }

  return { level: 'normal', final: true, reason: { key: 'sum.now.normal' } }
}

// ---------- B. This place: exposure ----------
export interface HistHit { event: string; gauge: string; gaugeId: string; status: Status; peak_ft: number | null }

/** E3: moderate/major peak at the nearest gauge within 3 mi. Worst first. */
export function historyHit(h: FloodHistory | null): HistHit | null {
  const evs = (Array.isArray(h?.events) ? h!.events : []).filter((e) => {
    const g = e?.nearest_gauge
    return g && (g.peak_category === 'moderate' || g.peak_category === 'major') && typeof g.distance_mi === 'number' && g.distance_mi <= 3
  })
  if (!evs.length) return null
  evs.sort((a, b) => LEVEL_RANK[gaugeLevel(b.nearest_gauge!.peak_category)] - LEVEL_RANK[gaugeLevel(a.nearest_gauge!.peak_category)])
  const e = evs[0], g = e.nearest_gauge!
  return { event: e.name, gauge: g.name, gaugeId: g.id, status: g.peak_category, peak_ft: g.peak_ft }
}

export interface ExposureResult { exposure: Exposure; final: boolean; reason: Reason }

export function exposure(i: SummaryInputs): ExposureResult {
  const { risk, hist } = i
  if (!risk.done) return { exposure: 'unknown', final: false, reason: { key: 'sum.checking' } }
  if (risk.failed || !risk.data) return { exposure: 'unknown', final: true, reason: { key: 'sum.exp.unknown' } }
  const r = risk.data
  const sfha = r.sfha === true, harvey = r.harvey?.flooded === true
  if (sfha && harvey) return { exposure: 'high', final: true, reason: { key: 'sum.exp.both' } }
  if (sfha) return { exposure: 'high', final: true, reason: { key: 'sum.exp.sfha' } }
  if (harvey) return { exposure: 'high', final: true, reason: { key: 'sum.exp.harvey' } }
  if (r.low_ground === true) return { exposure: 'elevated', final: true, reason: { key: 'sum.exp.low' } }
  if (r.reservoir_area) return { exposure: 'elevated', final: true, reason: { key: 'sum.exp.reservoir' } }
  if (!hist.done) return { exposure: 'unknown', final: false, reason: { key: 'sum.checking' } }
  const hit = historyHit(hist.data)
  if (hit) return { exposure: 'elevated', final: true, reason: { key: 'sum.exp.gauge', vars: { event: hit.event, status: '@gauge.' + hit.status } } }
  return { exposure: 'lower', final: true, reason: { key: 'sum.exp.lower' } }
}

// ---------- Why chips (in the order of the rules table) ----------
export type ChipKind =
  | 'fema' | 'harvey' | 'harveyNo' | 'gaugeHist' | 'zipClaims' | 'lowGround' | 'reservoir'
  | 'alert' | 'outlook' | 'gaugeNow' | 'unavailable'
export interface Chip { id: string; kind: ChipKind; tone: Level | 'neutral'; vars: Record<string, string>; source?: string }

export const NOAA_GAUGE = (id: string) => `https://water.noaa.gov/gauges/${encodeURIComponent(id.toLowerCase())}`
export const SRC = {
  sfha: 'https://www.law.cornell.edu/cfr/text/12/part-339/appendix-A',
  notSfha: 'https://communityimpact.com/news/2018/06/08/hurricane-harvey-damage-report-harris-county',
  flat: 'https://maapnext.harriscountytx.gov/Understand-Your-Risk',
  dams: 'https://www.texastribune.org/2017/09/28/could-houstons-dams-have-failed-during-harvey/',
  nws: 'https://www.weather.gov/',
  epqs: 'https://epqs.nationalmap.gov/v1/docs',
  noaaGauges: 'https://water.noaa.gov/',
} as const

export function whyChips(i: SummaryInputs): Chip[] {
  const out: Chip[] = []
  const r = i.risk.data
  if (r) {
    if (r.fema_zone) out.push({ id: 'fema', kind: 'fema', tone: r.sfha ? 'danger' : 'neutral', vars: { zone: r.fema_zone }, source: r.sfha ? SRC.sfha : SRC.notSfha })
    if (r.harvey?.flooded === true) out.push({ id: 'harvey', kind: 'harvey', tone: 'danger', vars: {}, source: r.harvey.source })
    if (r.harvey?.flooded === false) out.push({ id: 'harveyNo', kind: 'harveyNo', tone: 'neutral', vars: {}, source: r.harvey.source })
  }
  const hit = historyHit(i.hist.data)
  if (hit) out.push({ id: 'gaugeHist', kind: 'gaugeHist', tone: gaugeLevel(hit.status), vars: { event: hit.event, gauge: hit.gauge, status: '@gauge.' + hit.status, peak: hit.peak_ft != null ? String(hit.peak_ft) : '' }, source: NOAA_GAUGE(hit.gaugeId) })
  const z = i.zip?.data
  if (z && (z.claims?.since_2017 ?? 0) >= 1) out.push({ id: 'zip', kind: 'zipClaims', tone: 'neutral', vars: { zip: String(z.zip), n: String(z.claims.total ?? 0), m: String(z.claims.since_2017 ?? 0) }, source: z.source })
  if (r?.low_ground === true) out.push({ id: 'low', kind: 'lowGround', tone: 'watch', vars: {}, source: SRC.flat })
  if (r?.reservoir_area) out.push({ id: 'res', kind: 'reservoir', tone: 'watch', vars: {}, source: SRC.dams })
  const flood = alertsOf(i.alerts.data).filter((a) => isFloodAlert(a.event))
  flood.slice(0, 2).forEach((a, n) => out.push({ id: 'alert' + n, kind: 'alert', tone: alertLevel(a.event), vars: { event: a.event }, source: SRC.nws }))
  const day1 = i.outlook.data?.day1
  if (day1 && day1.category && day1.category !== 'None') {
    out.push({ id: 'outlook', kind: 'outlook', tone: day1.category === 'Moderate' || day1.category === 'High' ? 'watch' : 'neutral', vars: { category: '@sum.cat.' + day1.category, label: day1.label ?? '' }, source: i.outlook.data?.source })
  }
  gaugesOf(r).filter((g) => g.status === 'action' || g.status === 'minor' || g.status === 'moderate' || g.status === 'major')
    .forEach((g) => out.push({ id: 'g-' + g.id, kind: 'gaugeNow', tone: gaugeLevel(g.status), vars: { gauge: g.name, status: '@gauge.' + g.status, stage: g.stage_ft != null ? String(g.stage_ft) : '' }, source: NOAA_GAUGE(g.id) }))
  // Endpoints that failed: a muted chip instead of their signal.
  const un = (id: string, what: string) => out.push({ id: 'un-' + id, kind: 'unavailable', tone: 'neutral', vars: { what: '@sum.un.' + what } })
  if (i.risk.failed) { un('risk', 'risk'); un('gauges', 'gauges') }
  if (i.hist.failed) un('hist', 'hist')
  if (i.zip?.failed) un('zip', 'zip')
  if (i.alerts.failed) un('alerts', 'alerts')
  if (i.outlook.failed) un('outlook', 'outlook')
  return out
}

/** Endpoints still loading (for skeleton chips). */
export const pendingCount = (i: SummaryInputs) =>
  [i.risk, i.alerts, i.outlook, i.hist, i.zip].filter((s) => s && !s.done).length
export const anyFailed = (i: SummaryInputs) => [i.risk, i.alerts, i.outlook, i.hist, i.zip].some((s) => s?.failed)

// ---------- Top actions (§4.4) ----------
export type ActionId = 'drive' | 'alerts' | 'medical' | 'evac' | 'insurance' | 'renter' | 'plan' | 'ask'
export const ACTION_HREF: Record<ActionId, string> = {
  drive: '#drive', alerts: '#alerts', medical: '#prepare/medical', evac: '#prepare/evacuate',
  insurance: '#prepare/insurance', renter: '#prepare/renters', plan: '#prepare/plan', ask: '#ask',
}
export interface ActionCtx {
  now: Level; exposure: Exposure; household: Household
  hasPush: boolean; hasPlan: boolean
  /** action id -> ISO date marked done */
  done: Record<string, string>
  /** ISO date the current place was saved (insurance reappears when the place changes) */
  placeSavedAt: string | null
  today?: number
}
const DAY = 86_400_000

export function isDone(id: ActionId, c: Pick<ActionCtx, 'done' | 'placeSavedAt' | 'today'>): boolean {
  const at = Date.parse(c.done[id] ?? '')
  if (isNaN(at)) return false
  if (id === 'insurance') return !c.placeSavedAt || at >= Date.parse(c.placeSavedAt)
  return (c.today ?? Date.now()) - at < 90 * DAY
}

/** Matching actions in priority order: the first 3 not done, and the done ones. */
export function topActions(c: ActionCtx): { active: ActionId[]; done: ActionId[] } {
  const h = c.household, m = h.medical
  const medical = m.dialysis || m.oxygen || m.powerDevice
  const rules: [ActionId, boolean][] = [
    ['drive', LEVEL_RANK[c.now] >= LEVEL_RANK.watch],
    ['alerts', !c.hasPush],
    ['medical', medical],
    ['evac', h.hasCar === false || h.mobility !== 'none' || medical || !!m.other.trim()],
    ['insurance', c.exposure === 'high' || c.exposure === 'elevated' || h.renter === true],
    ['renter', h.renter === true],
    ['plan', !c.hasPlan],
    ['ask', true],
  ]
  const match = rules.filter(([, ok]) => ok).map(([id]) => id)
  const done = match.filter((id) => isDone(id, c))
  return { active: match.filter((id) => !done.includes(id)).slice(0, 3), done }
}

/** Which backup to line up: dialysis / oxygen / power (first checked). */
export const medicalKind = (h: Household): 'dialysis' | 'oxygen' | 'power' =>
  h.medical.dialysis ? 'dialysis' : h.medical.oxygen ? 'oxygen' : 'power'

/** Straight-line distance in miles. */
export function milesBetween(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const R = 3958.8, rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad, dLon = (b.lon - a.lon) * rad
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(s))
}

/** Translate `key` and fill {placeholders}. Values starting with "@" are i18n keys themselves. */
export function fill(t: (k: string) => string, key: string, vars: Record<string, string | number> = {}): string {
  let s = t(key)
  for (const [k, v] of Object.entries(vars)) {
    const val = typeof v === 'string' && v.startsWith('@') ? t(v.slice(1)) : String(v)
    s = s.split('{' + k + '}').join(val)
  }
  return s
}
export const fillReason = (t: (k: string) => string, r: Reason) => fill(t, r.key, r.vars)

export const timeOf = (ms: number, lang: string) => {
  try { return new Date(ms).toLocaleTimeString(lang, { hour: 'numeric', minute: '2-digit' }) } catch { return new Date(ms).toLocaleTimeString() }
}

/** One-line preview for the profile disclosure, e.g. "FEMA Zone AE · Flooded in Harvey (2017) · City of Houston rules". */
export function profilePreview(r: Risk | null, t: (k: string) => string): string {
  if (!r) return ''
  return [
    r.fema_zone ? fill(t, 'chip.fema', { zone: r.fema_zone }) : null,
    r.harvey?.flooded === true ? t('chip.harvey') : r.harvey?.flooded === false ? t('chip.harveyNo') : null,
    r.jurisdiction ? fill(t, 'det.profileRules', { j: r.jurisdiction }) : null,
  ].filter(Boolean).join(' · ')
}
