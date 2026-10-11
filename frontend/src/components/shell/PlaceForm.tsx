import { useState } from 'react'
import { MapPin } from 'lucide-react'
import { ApiError, api } from '../../api'
import { useApp } from '../../ctx'
import { NICKNAMES, usePlace, type MyPlace } from '../../state/place'
import { Button, ErrorBox, Field, Input, Segmented } from '../ds'

type Nick = (typeof NICKNAMES)[number]

/** Address + "Name this place" -> geocode -> setPlace. Used by Welcome and the My place sheet. */
export function PlaceForm({ onSaved, submitLabel, autoFocus }: { onSaved?: (p: MyPlace) => void; submitLabel?: string; autoFocus?: boolean }) {
  const { t } = useApp()
  const { place, setPlace } = usePlace()
  const preset = (NICKNAMES as readonly string[]).includes(place?.nickname ?? 'Home') ? (place?.nickname ?? 'Home') as Nick : 'Other'
  const [nick, setNick] = useState<Nick>(preset)
  const [custom, setCustom] = useState(preset === 'Other' ? place?.nickname ?? '' : '')
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = q.trim()
    if (!text) { setErr(t('place.needAddress')); return }
    setBusy(true); setErr(null)
    try {
      const g = await api.geocode(text)
      const nickname = nick === 'Other' ? (custom.trim() || 'Other') : nick
      const next: MyPlace = { lat: g.lat, lon: g.lon, label: g.matched_address || text, nickname, zip: null, savedAt: '' }
      setPlace(next)
      setQ('')
      onSaved?.(next)
    } catch (e2) {
      setErr(e2 instanceof ApiError && e2.status === 0 ? t('offline') : t('place.notFound'))
    } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <Field label={t('place.address')}>
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('addressHint')} autoComplete="street-address"
          enterKeyHint="search" autoFocus={autoFocus} aria-invalid={!!err || undefined} />
      </Field>
      <div>
        <p className="mb-1 text-body-sm font-medium text-ink">{t('place.name')}</p>
        <Segmented label={t('place.name')} value={nick} onChange={setNick}
          options={NICKNAMES.map((n) => ({ value: n, label: t('nick.' + n) }))} />
        {nick === 'Other' && (
          <Input className="mt-2" value={custom} onChange={(e) => setCustom(e.target.value)} maxLength={40}
            aria-label={t('place.customName')} placeholder={t('place.customName')} />
        )}
      </div>
      {err && <ErrorBox error={err} />}
      <Button type="submit" icon={MapPin} loading={busy} full>{submitLabel ?? t('place.save')}</Button>
    </form>
  )
}
