import { api, apiC20, type Evac, type FloodHistory, type Risk, type ZipInsurance, type Crossings } from '../../api'
import { zipOf } from '../../state/place'

export interface Col {
  risk: Risk | null; hist: FloodHistory | null; evac: Evac | null; zip: ZipInsurance | null; zipCode: string | null
  crossings: number | null
}
const ok = <T,>(p: Promise<T>) => p.then((v) => v, () => null as T | null)
let cross: Promise<Crossings | null> | null = null
const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, dx = (b.lon - a.lon) * r * Math.cos(a.lat * r), dy = (b.lat - a.lat) * r
  return Math.hypot(dx, dy) * 3958.8
}
export async function loadCol(p: { lat: number; lon: number; label: string }): Promise<Col> {
  const [risk, evac, c] = await Promise.all([ok(api.risk(p)), apiC20.evac(p), (cross ??= ok(api.crossings()))])
  const zipCode = zipOf(p.label)
  const [hist, zip] = await Promise.all([ok(api.floodHistory(p, zipCode ?? undefined)), zipCode ? ok(api.zipInsurance(zipCode)) : Promise.resolve(null)])
  let crossings: number | null = null
  if (c) crossings = c.features.filter((f) => f.geometry.type === 'Point' && km(p, { lon: (f.geometry.coordinates as number[])[0], lat: (f.geometry.coordinates as number[])[1] }) <= 2).length
  return { risk, hist, evac, zip, zipCode, crossings }
}
