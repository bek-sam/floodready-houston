import { api, apiC20, type Evac, type FloodHistory, type Risk, type ZipInsurance, type Crossings } from '../../api'
import { zipOf } from '../../state/place'

export interface Col {
  risk: Risk | null; hist: FloodHistory | null; evac: Evac | null; zip: ZipInsurance | null; zipCode: string | null
  crossings: number | null; pending?: boolean
}
const ok = <T,>(p: Promise<T>) => p.then((v) => v, () => null as T | null)
let cross: Promise<Crossings | null> | null = null
const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, dx = (b.lon - a.lon) * r * Math.cos(a.lat * r), dy = (b.lat - a.lat) * r
  return Math.hypot(dx, dy) * 3958.8
}
export async function loadCol(p: { lat: number; lon: number; label: string }, onPartial?: (c: Col) => void): Promise<Col> {
  const zipCode = zipOf(p.label)
  const cur: Col = { risk: null, hist: null, evac: null, zip: null, zipCode, crossings: null, pending: true }
  const push = (patch: Partial<Col>) => { Object.assign(cur, patch); onPartial?.({ ...cur }) }
  const crossingsCount = (c: Crossings | null) => c ? c.features.filter((f) => f.geometry.type === 'Point' && km(p, { lon: (f.geometry.coordinates as number[])[0], lat: (f.geometry.coordinates as number[])[1] }) <= 2).length : null
  await Promise.all([
    ok(api.risk(p)).then((risk) => push({ risk })),
    ok(apiC20.evac(p)).then((evac) => push({ evac })),
    (cross ??= ok(api.crossings())).then((c) => push({ crossings: crossingsCount(c) })),
    ok(api.floodHistory(p, zipCode ?? undefined)).then((hist) => push({ hist })),
    zipCode ? ok(api.zipInsurance(zipCode)).then((zip) => push({ zip })) : Promise.resolve(),
  ])
  cur.pending = false
  return { ...cur }
}
