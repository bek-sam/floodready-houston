// Render backend-coded strings. The API sends English text plus a stable `code` and `params`;
// we render t(code, params) when the key exists in the dictionary and fall back to the English text otherwise.
import { dicts } from '../i18n'
import { useApp } from '../ctx'
import type { Hazard, RouteCheck } from '../api'

export type Params = Record<string, unknown> | null | undefined
export type Bk = (code?: string | null, params?: Params, fallback?: string | null) => string

const DATE_KEYS = new Set(['pd', 'eff', 'end'])
const ISO = /^\d{4}-\d{2}-\d{2}$/

export function makeBk(lang: string, t: (k: string) => string): Bk {
  const has = (k: string) => k in (dicts[lang] ?? {}) || (lang === 'en' && k in dicts.en)
  return (code, params, fallback) => {
    if (!code || !has(code)) return fallback ?? ''
    let s = t(code)
    for (const [k, raw] of Object.entries(params ?? {})) {
      let v = raw == null ? '' : String(raw)
      if (k === 'status' && has('gauge.' + v)) v = t('gauge.' + v)
      else if (k === 'sim') v = v ? t('watch.sim') : ''
      else if (DATE_KEYS.has(k) && ISO.test(v)) v = new Date(v + 'T12:00:00').toLocaleDateString(lang, { month: 'short', day: 'numeric' })
      s = s.split('{' + k + '}').join(v)
    }
    return s
  }
}

export const useBk = (): Bk => { const { lang, t } = useApp(); return makeBk(lang, t) }

/** Rendered text of a coded `<field>` / `<field>_code` / `<field>_params` triple on an API object. */
export const coded = (bk: Bk, o: Record<string, unknown> | null | undefined, field: string): string =>
  bk(o?.[field + '_code'] as string, (o?.[field + '_params'] ?? o?.params) as Params, o?.[field] as string)

/** Warnings aligned with `warning_codes` (empty code keeps the English text). */
export const warningTexts = (bk: Bk, items?: string[], codes?: string[]): string[] =>
  (Array.isArray(items) ? items : []).map((w, i) => bk(codes?.[i], {}, w))

/** Short, length-capped hazard name (prefers backend short_name). */
export function hazName(bk: Bk, h: Hazard): string {
  const n = (h.name_code ? bk(h.name_code, {}, h.name) : h.short_name || h.name) || ''
  return n.length > 80 ? n.slice(0, 77).trimEnd() + '…' : n
}

export function hazardReason(bk: Bk, h: Hazard): string {
  return bk(h.reason_code, h.reason_params, h.reason)
}

/** The route-check verdict sentence, localized, with the community-report suffix. */
export function routeMessage(bk: Bk, t: (k: string) => string, r: RouteCheck): string {
  if (!r.message_code) return r.message
  const hz = r.hazards ?? []
  const names = hz.slice(0, 3).map((h) => hazName(bk, h) || t('route.unnamed')).join(', ') + (hz.length > 3 ? ' ' + t('p29.more').replace('{n}', String(hz.length - 3)) : '')
  const conds = (r.conditions ?? []).map((c) => bk(c.code, c.params)).join('; ')
  let s = bk(r.message_code, { ...(r.message_params ?? {}), names, conds }, r.message)
  const n = r.report_count ?? 0
  if (n > 0 && s !== r.message) s += ' ' + bk(n === 1 ? 'route.rep1' : 'route.repN', { n })
  else if (n > 0) s = r.message
  return s
}
