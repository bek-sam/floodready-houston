// Types and fetch helpers matching the API contract in CLAUDE.md. Base path: /api

export type Status = 'normal' | 'action' | 'minor' | 'moderate' | 'major' | 'unknown'
export interface FloodStages { action: number | null; minor: number | null; moderate: number | null; major: number | null }
export type FreshnessKind = 'live' | 'recent' | 'cached' | 'snapshot' | 'historical'
export interface Meta { as_of: string; source: string; freshness: FreshnessKind; snapshot_date?: string; storm_mode?: boolean }
export interface GaugeFlags { stale?: boolean; provisional?: boolean; spike?: boolean; offline?: boolean }
export interface GaugeImpact {
  current: { stage: number; statement: string } | null; next: { stage: number; statement: string } | null
  harvey_crest_ft: number | null; harvey_delta_ft: number | null; source?: string
}
export interface Gauge extends GaugeFlags {
  id: string; name: string; lat: number; lon: number
  stage_ft: number | null; observed_at: string | null
  flood_stages: FloodStages; status: Status
  impact?: GaugeImpact | null
}
export interface SourceHealth {
  name: string; last_success: string | null; last_error: string | null; p50_ms: number | null
  circuit: 'closed' | 'half_open' | 'open' | 'unknown' | 'unconfigured' | 'not_used'
}
export interface StatusReport { sources: SourceHealth[]; snapshots: Record<string, string | null>; storm_mode: boolean; meta: Meta }
export interface Coded { code?: string; params?: Record<string, unknown> }
export interface Fact extends Coded { text: string; source: string }
export interface Warned { warnings?: string[]; warning_codes?: string[] }
export interface Geocode extends Warned { lat: number | null; lon: number | null; matched_address: string | null; place?: string }
export interface Harvey { flooded: boolean | null; source?: string; note?: string; note_code?: string }
export interface Risk extends Warned {
  meta?: Meta
  harvey?: Harvey | null
  fema_zone: string | null; zone_subtype: string | null; sfha: boolean | null
  elevation_ft: number | null; elevation_source?: 'usgs_epqs' | 'open_meteo_approx'; low_ground: boolean | null; low_ground_note?: string | null; low_ground_note_code?: string; low_ground_note_params?: Record<string, unknown>
  jurisdiction_code?: string; jurisdiction_params?: Record<string, unknown>
  nearest_gauges: Gauge[]; reservoir_area: string | boolean | null; jurisdiction: string | null
  facts: Fact[]
}
export interface FloodHistory extends Warned {
  harvey: { flooded: boolean | null; source?: string } | null
  events: { id: string; name: string; start: string; nearest_gauge: { id: string; name: string; distance_mi: number; peak_ft: number | null; peak_category: Status } | null }[]
  zip: { zip: string; peak_year: number | null; peak_year_claims: number | null } | null
}
export interface Alert { event: string; severity: string; headline: string; description: string; expires: string | null }
export interface Alerts extends Warned { alerts: Alert[]; meta?: Meta }

export interface CrossingProps { id: string; name: string; risk: 'high' | 'medium'; reasons: string[]; reason_codes?: ({ code: string; params?: Record<string, unknown> } | null)[]; sources: string[] }
export interface CrossingFeature {
  type: 'Feature'; properties: CrossingProps
  geometry: { type: 'Point'; coordinates: [number, number] } | { type: string; coordinates: unknown }
}
export interface Crossings { type: 'FeatureCollection'; features: CrossingFeature[] }

export interface LatLon { lat: number; lon: number }
export interface Hazard { kind?: string; crossing_id: string; name: string; lat: number; lon: number; reason: string; reason_code?: string | null; reason_params?: Record<string, unknown>; name_code?: string }
export interface RouteCheck extends Warned {
  route: { type: 'LineString'; coordinates: [number, number][] } | null
  hazards: Hazard[]; verdict: 'safe' | 'caution' | 'avoid'; message: string; meta?: Meta
  message_code?: string; message_params?: Record<string, unknown>; conditions?: { code: string; params?: Record<string, unknown> }[]; report_count?: number
}

export interface ReplayEvent { id: string; name: string; start: string; end: string; summary: string; source: string }
export interface ReplayGauge {
  id: string; name: string; lat: number; lon: number
  flood_stages: FloodStages; series: { t: string; stage_ft: number }[]
}
export interface Replay { event: ReplayEvent; gauges: ReplayGauge[] }

export interface History { id: string; name: string; readings: { t: string; stage_ft: number }[]; flood_stages: FloodStages; source: 'db' | 'live' }

export interface Countdown {
  purchase_date: string; effective_date: string; days_wait: number; season_end: string
  covered_before_season_end: boolean; message: string; exceptions_note?: string; exceptions_note_code?: string; message_code?: string; message_params?: Record<string, unknown>; source: string
}
export interface Profile {
  id?: string; language: string; age_group: string; mobility: string
  medical: string[]; has_car: boolean; pets: boolean; renter: boolean; address: string
}
export type When = 'now' | 'storm_watch' | 'storm' | 'after'
export interface Plan extends Warned { steps: { title: string; detail: string; when: When }[]; generated_by: string }
export interface Ask extends Warned { answer: string; sources: string[]; citations?: { sentence_index: number; source_index: number }[]; uncited?: number[]; generated_by: string; tools_used?: string[]; tools?: string[]; speak?: string }
export interface Report { id?: string; lat: number; lon: number; kind: string; depth_in: number | null; note: string; created_at?: string }
export interface BondProject { name: string; status?: string; budgeted?: number | null; spent?: number | null; distance_mi?: number | null; url?: string }
export interface Civic extends Warned {
  bond: { facts: Fact[]; projects: BondProject[] }
  reservoir: { in_area: boolean; facts: Fact[]; note?: string; note_code?: string }
  responsibility: { issue: string; agency: string; contact: string; code?: string }[]
  officials?: { commissioner?: Official | null; council?: Official | null; floodplain_admin?: Official | null } | null
}
export interface Official { name?: string; title?: string; office?: string; phone?: string; email?: string; url?: string; district?: string; precinct?: string | number; entity?: string }
export interface BuyoutArea { in_buyout_area: boolean | null; area_name?: string | null; source?: string; note?: string; note_code?: string; params?: Record<string, unknown> }

export interface WatchPlace { id: string; label: string; lat: number; lon: number; lang: string }
export type WatchLevel = 'ok' | 'watch' | 'warning'
export interface WatchStatus {
  id: string; label: string; level: WatchLevel; reasons: string[]; reason_codes?: { code: string; params?: Record<string, unknown> }[]; message_code?: string; message_params?: Record<string, unknown>; alerts: Alert[]; gauges: Gauge[]
  crossings_nearby: number; message: string; meta?: Meta
}
export interface Shelter {
  name: string; address: string; county: string; status_2017?: string | null
  capacity: number | null; occupancy: number | null; pet_friendly: boolean
  lat: number; lon: number; distance_mi: number | null
}
export interface Shelters extends Warned { shelters: Shelter[]; any_open: boolean; historical?: boolean; data_as_of?: string; source: string; note: string; note_code?: string }
export interface Outlook extends Warned {
  day1: { category: 'None' | 'Marginal' | 'Slight' | 'Moderate' | 'High'; label: string } | null
  days?: { day: number; category: 'None' | 'Marginal' | 'Slight' | 'Moderate' | 'High' | null; label?: string; valid_time?: string | null }[]
  max_category?: string | null; prepare_nudge?: boolean
  source: string; note: string; note_code?: string
}
export interface Nri extends Warned {
  available?: boolean; tract?: string; population?: number
  inland_flood?: { rating: string | null }; resilience?: { rating: string | null }; social_vulnerability?: { rating: string | null }
  source?: string; note?: string
}
export interface ParkingCheck extends Warned {
  lat: number; lon: number; address?: string | null; verdict: 'move' | 'no_flags'; headline: string; detail: string
  reasons: { code: string; text: string }[]; fema_zone: string | null; harvey_flooded: boolean | null; elevation_ft: number | null
  crossings_within_300m: { name: string; distance_m: number; risk: string }[]; active_flood_alerts: number | null
  higher_ground: { lat: number; lon: number; elevation_ft: number | null; gain_ft: number | null; distance_m: number | null; maps_url: string } | null
  limits: string; sources: string[]; meta?: Meta
}
export interface DemoRoute { label: string; origin: LatLon; destination: LatLon }

export interface ZipInsurance extends Warned {
  zip: string
  claims: { total: number; since_2017: number; by_year: { year: number; count: number }[] }
  policies_in_force: number | null; source: string; note: string; note_code?: string
  premiums?: { median_annual: number | null; p25: number | null; p75: number | null; sample_size?: number; source?: string; as_of?: string } | null
}
export interface MedFacility { name: string; address: string; phone: string | null; lat: number; lon: number; distance_mi: number }
export interface Medical { facilities: MedFacility[]; source: string; note: string }

export type StreamEvent =
  | { type: 'speak'; text: string }
  | ({ type: 'final' } & Ask & { timings?: { first_speak_ms?: number; total_ms?: number } })
  | { type: 'error'; detail?: string }

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch('/api' + path, init)
  } catch {
    throw new ApiError('offline', 0)
  }
  if (!res.ok) {
    let detail = ''
    try { detail = (await res.json()).detail ?? '' } catch { /* ignore */ }
    throw new ApiError(typeof detail === 'string' && detail ? detail : `Request failed (${res.status})`, res.status)
  }
  let body: unknown
  try { body = await res.json() } catch { throw new ApiError('Unexpected response from server', res.status) }
  if (body == null || typeof body !== 'object') throw new ApiError('Unexpected response from server', res.status)
  return body as T
}
const post = <T,>(path: string, body: unknown, signal?: AbortSignal) =>
  req<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal })
const q = (o: { q: string } | { purchase_date: string } | LatLon) => new URLSearchParams(Object.entries(o).filter(([k]) => k !== 'label').map(([k, v]) => [k, String(v)])).toString()

export const api = {
  geocode: async (s: string) => {
    const g = await req<Geocode>('/geocode?' + q({ q: s }))
    if (g.lat == null || g.lon == null) throw new ApiError(g.warnings?.join('. ') || 'Address not found', 404)
    return g as Geocode & { lat: number; lon: number }
  },
  risk: (p: LatLon) => req<Risk>('/risk?' + q(p)),
  floodHistory: (p: LatLon, zip?: string) => req<FloodHistory>('/flood-history?' + q(p) + (zip ? '&zip=' + encodeURIComponent(zip) : '')),
  status: () => req<StatusReport>('/status'),
  alerts: (p: LatLon) => req<Alerts>('/alerts?' + q(p)),
  crossings: () => req<Crossings>('/crossings'),
  routeCheck: (origin: LatLon, destination: LatLon, simulate: boolean) =>
    post<RouteCheck>('/route-check' + (simulate ? '?simulate=storm' : ''), { origin, destination }),
  watchSave: (p: { label: string; lat: number; lon: number; lang: string }) => post<WatchPlace>('/watch', p),
  watchStatus: (ids: string[], simulate: boolean, signal?: AbortSignal) =>
    req<{ places: WatchStatus[] }>('/watch/status?ids=' + encodeURIComponent(ids.join(',')) + (simulate ? '&simulate=storm' : ''), { signal }),
  shelters: (p: LatLon, petFriendly = false, limit = 10) =>
    req<Shelters>('/shelters?' + q(p) + `&pet_friendly=${petFriendly}&limit=${limit}`),
  parkingCheck: (p: LatLon | { q: string }) => req<ParkingCheck>('/parking/check?' + q(p)),
  outlook: (p: LatLon) => req<Outlook>('/outlook?' + q(p)),
  routeDemo: () => req<DemoRoute[]>('/route-check/demo'),
  vapidKey: () => req<{ key: string }>('/push/vapid-public-key'),
  pushSubscribe: (subscription: unknown, place_ids: string[], lang: string) => post<{ id: string }>('/push/subscribe', { subscription, place_ids, lang }),
  pushUnsubscribe: (endpoint: string) => post<{ ok: boolean }>('/push/unsubscribe', { endpoint }),
  pushTest: (endpoint: string) => post<{ sent: number }>('/push/test', { endpoint }),
  pushSimulate: (endpoint: string) => post<{ sent: number }>('/push/simulate', { endpoint }),
  gaugeHistory: (id: string, hours = 48) => req<History>(`/gauges/${encodeURIComponent(id)}/history?hours=${hours}`),
  replayEvents: () => req<ReplayEvent[]>('/replay/events'),
  replay: (id: string) => req<Replay>('/replay/' + encodeURIComponent(id)),
  countdown: (d: string) => req<Countdown>('/insurance/countdown?' + q({ purchase_date: d })),
  saveProfile: (p: Profile) => post<Profile>('/profile', p),
  plan: (profile: Profile, lat: number, lon: number) => post<Plan>('/plan', { profile, lat, lon }),
  ask: (question: string, lang: string, loc?: LatLon | null, extra?: { history?: { role: 'user' | 'assistant'; content: string }[]; mode?: 'voice'; signal?: AbortSignal }) =>
    post<Ask>('/ask', { question, lang, ...(loc ? { lat: loc.lat, lon: loc.lon } : {}), ...(extra?.history?.length ? { history: extra.history } : {}), ...(extra?.mode ? { mode: extra.mode } : {}) }, extra?.signal),
  reports: () => req<Report[]>('/reports'),
  postReport: (r: Report) => post<Report>('/reports', r),
  zipInsurance: (zip: string) => req<ZipInsurance>('/zip-insurance?zip=' + encodeURIComponent(zip)),
  medical: (p: LatLon, limit = 5) => req<Medical>('/medical?' + q(p) + `&kind=dialysis&limit=${limit}`),
  buyoutArea: (p: LatLon) => req<BuyoutArea>('/buyout-area?' + q(p)),
  civic: (p?: LatLon | null) => req<Civic>('/civic' + (p ? '?' + q(p) : '')),
  voice: async (text: string, lang: string): Promise<Blob> => {
    const res = await fetch('/api/voice', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, lang }),
    })
    if (!res.ok) throw new ApiError('voice unavailable', res.status)
    return res.blob()
  },
  /** Sentence audio: try chunked /voice/stream, fall back to /voice. */
  voiceSentence: async (text: string, lang: string, signal?: AbortSignal): Promise<Blob> => {
    for (const path of ['/api/voice/stream', '/api/voice']) {
      try {
        const res = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, lang }), signal })
        if (res.ok) { const b = await res.blob(); if (b.size > 0) return b }
      } catch (e) { if (signal?.aborted) throw e }
    }
    throw new ApiError('voice unavailable', 503)
  },
  filler: async (lang: string): Promise<Blob> => {
    const res = await fetch('/api/voice/filler?lang=' + encodeURIComponent(lang))
    if (!res.ok) throw new ApiError('filler unavailable', res.status)
    return res.blob()
  },
  /** POST /ask/stream, parse SSE. Throws ApiError (404 => caller falls back to /ask). */
  askStream: async (
    question: string, lang: string, loc: LatLon | null | undefined,
    extra: { history?: { role: 'user' | 'assistant'; content: string }[]; signal?: AbortSignal },
    onEvent: (e: StreamEvent) => void,
  ): Promise<void> => {
    let res: Response
    try {
      res = await fetch('/api/ask/stream', {
        method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, signal: extra.signal,
        body: JSON.stringify({ question, lang, mode: 'voice', ...(loc ? { lat: loc.lat, lon: loc.lon } : {}), ...(extra.history?.length ? { history: extra.history } : {}) }),
      })
    } catch (e) { if (extra.signal?.aborted) throw e; throw new ApiError('offline', 0) }
    if (!res.ok || !res.body) {
      let detail = ''
      try { detail = (await res.json()).detail ?? '' } catch { /* ignore */ }
      throw new ApiError(typeof detail === 'string' && detail ? detail : `Request failed (${res.status})`, res.ok ? 500 : res.status)
    }
    const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = ''
    const handle = (chunk: string) => {
      const data = chunk.split('\n').filter((l) => l.startsWith('data:')).map((l) => l.slice(5).trimStart()).join('\n')
      if (!data) return
      try { const ev = JSON.parse(data); if (ev && typeof ev.type === 'string') onEvent(ev as StreamEvent) } catch { /* ignore bad frame */ }
    }
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true }).replace(/\r\n/g, '\n')
      let i: number
      while ((i = buf.indexOf('\n\n')) >= 0) { handle(buf.slice(0, i)); buf = buf.slice(i + 2) }
    }
    if (buf.trim()) handle(buf)
  },
}

export interface Evac { zone: 'A' | 'B' | 'C' | null; zone_status?: 'in_zone' | 'not_in_zone' | 'unavailable' | 'found' | 'none' | string; surge_status?: string; notes?: string[] | string | null; zone_label?: string | null; surge?: Record<string, string | null> | null; surge_ranges?: Record<string, { min_ft: number | null; max_ft: number | null; label: string } | null> | null; sources?: string[]; meta?: Meta }
export interface HwmMark { dry?: boolean; id: string | number; distance_mi: number; height_above_ground_ft: number | null; elevation_ft: number | null; site_desc: string | null; event: string | null; url: string | null }
export interface Hwm { marks: HwmMark[]; wet_marks?: HwmMark[]; dry_marks?: HwmMark[]; nearest_depth_ft: number | null; source?: string; meta?: Meta }
export interface Coastal {
  tide: { station: string; observed_ft: number | null; predicted_ft: number | null; anomaly_ft: number | null; as_of: string | null } | null
  active_storms: { name: string; type: string; advisory_url: string | null; relevant?: boolean; gulf_of_mexico?: boolean }[]; meta?: Meta
}
/** Cycle 20 endpoints: any failure (404, offline) resolves to null so the card is simply hidden. */
const soft = <T,>(path: string) => req<T>(path).catch(() => null as T | null)
export const apiC20 = {
  evac: (p: { lat: number; lon: number }) => soft<Evac>(`/evac?lat=${p.lat}&lon=${p.lon}`),
  nri: (p: { lat: number; lon: number }) => soft<Nri>(`/nri?lat=${p.lat}&lon=${p.lon}`),
  hwm: (p: { lat: number; lon: number }) => soft<Hwm>(`/hwm?lat=${p.lat}&lon=${p.lon}&radius_mi=2`),
  coastal: () => soft<Coastal>('/coastal'),
}

export function errText(e: unknown, offlineMsg: string): string {
  if (e instanceof ApiError) return e.status === 0 ? offlineMsg : e.message
  return e instanceof Error ? e.message : String(e)
}

/** Status of a stage value against flood stages (used by Replay). */
export function statusFor(stage: number | null | undefined, fs: FloodStages | null | undefined): Status {
  if (stage == null || !fs) return 'unknown'
  if (fs.major != null && stage >= fs.major) return 'major'
  if (fs.moderate != null && stage >= fs.moderate) return 'moderate'
  if (fs.minor != null && stage >= fs.minor) return 'minor'
  if (fs.action != null && stage >= fs.action) return 'action'
  return 'normal'
}
