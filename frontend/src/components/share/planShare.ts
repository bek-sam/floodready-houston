import { DEFAULT_HOUSEHOLD, type Household } from '../../state/place'

export interface Contact { name: string; phone: string }
export interface FamilyExtras { meeting: string; contacts: Contact[] }
export interface SharedPlan extends FamilyExtras { household: Household }
export const FAMILY_KEY = 'floodready.familyplan.v1'
export const MAX_JSON = 1500

const str = (v: unknown, max: number) => (typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f<>]/g, '').trim().slice(0, max) : '')
const bool = (v: unknown) => v === true

/** Validate every field of untrusted input. Strings are only ever rendered as text. */
export function sanitizePlan(raw: unknown): SharedPlan | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, any>
  if (o.v !== 1) return null
  const h = o.h && typeof o.h === 'object' ? o.h : {}
  const m = h.medical && typeof h.medical === 'object' ? h.medical : {}
  const a = h.ages && typeof h.ages === 'object' ? h.ages : {}
  const tri = (v: unknown) => (v === true ? true : v === false ? false : null)
  const household: Household = {
    ...DEFAULT_HOUSEHOLD,
    renter: tri(h.renter), hasCar: tri(h.hasCar),
    medical: { dialysis: bool(m.dialysis), oxygen: bool(m.oxygen), powerDevice: bool(m.powerDevice), other: str(m.other, 80) },
    mobility: h.mobility === 'some' || h.mobility === 'wheelchair' ? h.mobility : 'none',
    ages: { kids: bool(a.kids), older: bool(a.older) }, pets: bool(h.pets),
  }
  const contacts = (Array.isArray(o.c) ? o.c : []).slice(0, 2).map((c: any) => ({ name: str(c?.n, 60), phone: str(c?.p, 20).replace(/[^\d+()\-\s]/g, '') })).filter((c: Contact) => c.name || c.phone)
  return { household, meeting: str(o.m, 160), contacts }
}

const b64u = (bytes: Uint8Array) => { let s = ''; bytes.forEach((b) => (s += String.fromCharCode(b))); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') }
const unb64u = (s: string) => { const b = atob(s.replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from(b, (c) => c.charCodeAt(0)) }

/** Returns the URL fragment ("#share=...") or null if too long. Phones are only included when asked. */
export function encodePlan(p: SharedPlan, includePhones: boolean): string | null {
  const json = JSON.stringify({ v: 1, h: p.household, m: p.meeting, c: p.contacts.map((c) => (includePhones ? { n: c.name, p: c.phone } : { n: c.name })) })
  if (json.length > MAX_JSON * 2) return null
  const frag = b64u(new TextEncoder().encode(json))
  return frag.length > MAX_JSON ? null : '#share=' + frag
}

/** Parse "#share=..." -> validated plan, or null for anything malformed. */
export function decodePlan(hash: string): SharedPlan | null {
  const m = /^#share=([A-Za-z0-9_-]{1,3000})$/.exec(hash)
  if (!m) return null
  try { return sanitizePlan(JSON.parse(new TextDecoder().decode(unb64u(m[1])))) } catch { return null }
}
