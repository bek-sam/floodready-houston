import { useEffect, useState } from 'react'
import { Phone, MessageSquare, Trash2, UserPlus } from 'lucide-react'
import { api, errText, type WatchLevel } from '../../api'
import { useApp } from '../../ctx'
import { Button, Card, ErrorBox, Field, inputCls } from '../ds'
import { store } from '../../state/place'

const KEY = 'floodready.buddies.v1'
const MAX = 5
interface Buddy { id: string; name: string; phone: string; address: string; needs: string; lat?: number; lon?: number; wid?: string; safeAt?: string | null }
const load = (): Buddy[] => { const v = store.json<unknown>(KEY, []); return Array.isArray(v) ? (v as Buddy[]).filter((b) => b && typeof b.name === 'string').slice(0, MAX) : [] }
const NEEDS = ['alone', 'oxygen', 'mobility', 'noCar'] as const
const digits = (s: string) => s.replace(/[^\d+]/g, '')

/** Neighbor check-in. Everything stays on this device; the only network call is the public watch status for a buddy's rounded coordinates (no name, no phone). */
export default function BuddySection() {
  const { t } = useApp()
  const [list, setList] = useState<Buddy[]>(load)
  const [level, setLevel] = useState<Record<string, WatchLevel>>({})
  const [adding, setAdding] = useState(false)
  const [f, setF] = useState({ name: '', phone: '', address: '', needs: [] as string[] })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const persist = (n: Buddy[]) => { setList(n); store.set(KEY, JSON.stringify(n)) }

  useEffect(() => {
    const ids = list.map((b) => b.wid).filter(Boolean) as string[]
    if (!ids.length) return
    const c = new AbortController()
    api.watchStatus(ids, false, c.signal).then((r) => {
      const m: Record<string, WatchLevel> = {}
      for (const s of r.places ?? []) m[s.id] = s.level
      setLevel(m)
    }).catch(() => {})
    return () => c.abort()
  }, [list.length]) // eslint-disable-line react-hooks/exhaustive-deps

  async function add(e: React.FormEvent) {
    e.preventDefault(); setErr(null); setBusy(true)
    const b: Buddy = { id: String(Date.now()), name: f.name.trim(), phone: digits(f.phone), address: f.address.trim(), needs: f.needs.join(',') }
    try {
      if (b.address) {
        const g = await api.geocode(b.address)
        const lat = Math.round(g.lat * 1000) / 1000, lon = Math.round(g.lon * 1000) / 1000
        b.lat = lat; b.lon = lon
        try { b.wid = (await api.watchSave({ label: 'Buddy', lat, lon, lang: 'en' })).id } catch { /* status just unavailable */ }
      }
      persist([...list, b]); setF({ name: '', phone: '', address: '', needs: [] }); setAdding(false)
    } catch (x) { setErr(errText(x, t('offline'))) } finally { setBusy(false) }
  }
  const toggleNeed = (n: string) => setF((p) => ({ ...p, needs: p.needs.includes(n) ? p.needs.filter((x) => x !== n) : [...p.needs, n] }))
  const setSafe = (b: Buddy) => persist(list.map((x) => (x.id === b.id ? { ...x, safeAt: x.safeAt ? null : new Date().toISOString() } : x)))

  return (
    <section aria-labelledby="buddy-h" className="mt-6">
      <h2 id="buddy-h" className="text-h2 text-ink">{t('p13.buddy.title')}</h2>
      <p className="mt-1 text-body-sm text-muted">{t('p13.buddy.sub')}</p>
      <div className="mt-3 space-y-3">
        {list.length === 0 && <p className="text-body-sm text-muted">{t('p13.buddy.empty')}</p>}
        {list.map((b) => {
          const lv = b.wid ? level[b.wid] : undefined
          const alert = lv === 'watch' || lv === 'warning'
          const msg = t('p13.buddy.sms').replace('{name}', b.name)
          return (
            <Card key={b.id} tone={alert ? lv : undefined}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-semibold text-ink">{alert ? t('p13.buddy.check').replace('{name}', b.name) : b.name}</p>
                  {alert && <p className="text-body-sm text-ink">{t('p13.buddy.alertAt')}</p>}
                  {b.needs && <p className="text-caption text-muted">{b.needs.split(',').filter(Boolean).map((n) => t('p13.need.' + n)).join(' · ')}</p>}
                </div>
                <button type="button" onClick={() => persist(list.filter((x) => x.id !== b.id))} aria-label={t('p13.buddy.remove').replace('{name}', b.name)} className="grid min-h-11 min-w-11 place-items-center text-muted"><Trash2 aria-hidden size={18} /></button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {b.phone && <a href={'tel:' + b.phone} className="inline-flex min-h-11 items-center gap-2 rounded-md border border-line px-3 text-body-sm font-medium text-brand"><Phone aria-hidden size={16} />{t('p13.buddy.call')}</a>}
                {b.phone && <a href={`sms:${b.phone}?&body=${encodeURIComponent(msg)}`} className="inline-flex min-h-11 items-center gap-2 rounded-md border border-line px-3 text-body-sm font-medium text-brand"><MessageSquare aria-hidden size={16} />{t('p13.buddy.text')}</a>}
                <label className="inline-flex min-h-11 items-center gap-2 text-body-sm text-ink">
                  <input type="checkbox" checked={!!b.safeAt} onChange={() => setSafe(b)} className="h-5 w-5" />
                  {b.safeAt ? t('p13.buddy.safeAt').replace('{time}', new Date(b.safeAt).toLocaleString()) : t('p13.buddy.markSafe')}
                </label>
              </div>
            </Card>
          )
        })}
      </div>
      {adding ? (
        <form onSubmit={add} className="mt-3 space-y-3 rounded-lg border border-line p-3">
          <Field label={t('p13.buddy.name')}><input className={inputCls} required maxLength={40} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoComplete="off" /></Field>
          <Field label={t('p13.buddy.phone')}><input className={inputCls} type="tel" inputMode="tel" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} autoComplete="off" /></Field>
          <Field label={t('p13.buddy.address')} hint={t('p13.buddy.privacy')}><input className={inputCls} value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} autoComplete="off" /></Field>
          <fieldset><legend className="mb-1 text-body-sm font-medium text-ink">{t('p13.buddy.needs')}</legend>
            <div className="flex flex-wrap gap-3">{NEEDS.map((n) => (
              <label key={n} className="inline-flex min-h-11 items-center gap-2 text-body-sm"><input type="checkbox" className="h-5 w-5" checked={f.needs.includes(n)} onChange={() => toggleNeed(n)} />{t('p13.need.' + n)}</label>
            ))}</div></fieldset>
          {err && <ErrorBox error={err} />}
          <div className="flex gap-2"><Button type="submit" loading={busy}>{t('p13.buddy.save')}</Button><Button type="button" variant="secondary" onClick={() => setAdding(false)}>{t('p13.cancel')}</Button></div>
        </form>
      ) : list.length < MAX ? (
        <Button className="mt-3" variant="secondary" icon={UserPlus} onClick={() => setAdding(true)}>{t('p13.buddy.add')}</Button>
      ) : <p className="mt-3 text-caption text-muted">{t('p13.buddy.max')}</p>}
      <p className="mt-2 text-caption text-muted">{t('p13.buddy.local')}</p>
    </section>
  )
}
