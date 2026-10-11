import { useState } from 'react'
import { api, errText } from '../api'
import { useApp } from '../ctx'
import { Btn, ErrorBox, Field, inputCls } from './ui'

export default function AddressForm({ onDone }: { onDone?: () => void }) {
  const { t, place, setPlace } = useApp()
  const [q, setQ] = useState(place?.label ?? '')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!q.trim()) return
    setBusy(true); setErr(null)
    try {
      const g = await api.geocode(q.trim())
      setPlace({ lat: g.lat, lon: g.lon, label: g.matched_address || q })
      onDone?.()
    } catch (e2) { setErr(errText(e2, t('offline'))) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={submit} className="space-y-2">
      <Field label={t('address')}>
        <input className={inputCls} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('addressHint')}
          autoComplete="street-address" />
      </Field>
      <Btn type="submit" disabled={busy}>{busy ? t('loading') : t('check')}</Btn>
      {err && <ErrorBox error={err} />}
    </form>
  )
}
