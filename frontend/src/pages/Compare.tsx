import { useEffect, useMemo, useState } from 'react'
import { useApp } from '../ctx'
import { api, errText } from '../api'
import { Button, ErrorBox, Field, PageHeader, inputCls } from '../components/ds'
import CompareTable, { type Named } from '../components/compare/CompareTable'
import { loadCol, type Col } from '../components/compare/useCompare'
import { placeName, store, streetOf, usePlace } from '../state/place'

interface Opt { id: string; name: string; lat: number; lon: number; label: string }
const MAXSEL = 3

export default function Compare() {
  const { t } = useApp()
  const { place } = usePlace()
  const opts = useMemo(() => {
    const o: Opt[] = []
    if (place) o.push({ id: 'mine', name: t('p13.cmp.mine'), lat: place.lat, lon: place.lon, label: place.label })
    const w = store.json<{ id: string; label: string; lat: number; lon: number }[]>('watchPlaces', [])
    if (Array.isArray(w)) for (const p of w) if (!place || Math.abs(p.lat - place.lat) > 1e-4 || Math.abs(p.lon - place.lon) > 1e-4) o.push({ id: 'w' + p.id, name: placeName(p.label.split(' · ')[0], t) + ' · ' + streetOf(p.label.split(' · ').pop() || p.label), lat: p.lat, lon: p.lon, label: p.label })
    return o
  }, [place, t])
  const [typed, setTyped] = useState<Opt[]>([])
  const all = [...opts, ...typed]
  const [sel, setSel] = useState<string[]>(() => (place ? ['mine'] : []))
  const [cols, setCols] = useState<Record<string, Col | 'err'>>({})
  const [addr, setAddr] = useState(''); const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    for (const id of sel) {
      const o = all.find((x) => x.id === id)
      if (!o || cols[id]) continue
      loadCol(o, (c) => setCols((p) => (p[id] && (p[id] as Col).pending === false ? p : { ...p, [id]: c }))).then((c) => setCols((p) => ({ ...p, [id]: c })), () => setCols((p) => ({ ...p, [id]: 'err' })))
    }
  }, [sel]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id: string) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length < MAXSEL ? [...s, id] : s))
  async function addTyped(e: React.FormEvent) {
    e.preventDefault(); if (!addr.trim()) return
    setBusy(true); setErr(null)
    try {
      const g = await api.geocode(addr); const id = 't' + Date.now()
      setTyped((p) => [...p, { id, name: streetOf(g.matched_address || addr), lat: g.lat, lon: g.lon, label: g.matched_address || addr }])
      setSel((s) => (s.length < MAXSEL ? [...s, id] : s)); setAddr('')
    } catch (x) { setErr(errText(x, t('offline'))) } finally { setBusy(false) }
  }
  const named: Named[] = sel.map((id) => { const o = all.find((x) => x.id === id); const c = cols[id]; return { name: o?.name ?? id, col: c && c !== 'err' ? c : null, err: c === 'err' } })

  return (
    <div>
      <PageHeader title={t('p13.cmp.title')} subtitle={t('p13.cmp.sub')} />
      <fieldset className="mb-4"><legend className="mb-1 text-body-sm font-medium text-ink">{t('p13.cmp.pick')}</legend>
        <div className="flex flex-wrap gap-3">{all.map((o) => (
          <label key={o.id} className="inline-flex min-h-11 items-center gap-2 text-body-sm text-ink">
            <input type="checkbox" className="h-5 w-5" checked={sel.includes(o.id)} disabled={!sel.includes(o.id) && sel.length >= MAXSEL} onChange={() => toggle(o.id)} />{o.name}
          </label>))}</div></fieldset>
      <form onSubmit={addTyped} className="mb-4 flex items-end gap-2">
        <Field label={t('p13.cmp.type')} className="flex-1"><input className={inputCls} value={addr} onChange={(e) => setAddr(e.target.value)} autoComplete="street-address" /></Field>
        <Button type="submit" loading={busy} disabled={sel.length >= MAXSEL}>{t('p13.cmp.add')}</Button>
      </form>
      {err && <ErrorBox error={err} />}
      {sel.length >= 2 ? <CompareTable cols={named} /> : <p className="text-body-sm text-muted">{t('p13.cmp.min')}</p>}
      <p className="mt-4 rounded-lg border border-line bg-surface-2 p-3 text-body-sm text-ink">
        {t('p13.cmp.rent')} <a className="font-medium text-brand underline" href="#prepare">{t('p13.cmp.letter')}</a>
      </p>
      <p className="mt-2 text-caption text-muted">{t('p13.cmp.disc')}</p>
    </div>
  )
}
