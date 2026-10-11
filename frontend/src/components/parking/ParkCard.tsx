import { useState } from 'react'
import { CalendarPlus, Car, MapPin, Trash2 } from 'lucide-react'
import { api, errText, type ParkingCheck } from '../../api'
import { useApp } from '../../ctx'
import { fill } from '../../lib/summary'
import { store, usePlace } from '../../state/place'
import { Button, ButtonLink, Card, ErrorBox, Input, SkeletonText } from '../ds'
import { fold, icsEscape } from '../season/ics'

const KEY = 'floodready.parking.v1'
interface Spot { lat: number; lon: number; label: string }
const loadSpot = (): Spot | null => {
  const v = store.json<Partial<Spot> | null>(KEY, null)
  return v && Number.isFinite(v.lat) && Number.isFinite(v.lon) && typeof v.label === 'string' ? (v as Spot) : null
}

/** Reminder .ics for tomorrow 8:00 local-floating time. */
function moveCarIcs(summary: string, desc: string): string {
  const d = new Date(Date.now() + 864e5), p = (n: number) => String(n).padStart(2, '0')
  const ds = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}T080000`
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//FloodReady//Park//EN', 'BEGIN:VEVENT', `UID:park-${Date.now()}@floodready`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]|\.\d+/g, '')}`, `DTSTART:${ds}`, `DTEND:${ds}`,
    fold('SUMMARY:' + icsEscape(summary)), fold('DESCRIPTION:' + icsEscape(desc)), 'END:VEVENT', 'END:VCALENDAR'].join('\r\n')
}

/** "Where should I park?" The parked spot is stored on this device only; the check uses public flood records. */
export default function ParkCard() {
  const { t } = useApp()
  const { place } = usePlace()
  const [spot, setSpot] = useState<Spot | null>(loadSpot)
  const [addr, setAddr] = useState('')
  const [res, setRes] = useState<ParkingCheck | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function run(p: { lat: number; lon: number } | { q: string }, label?: string) {
    setBusy(true); setErr(null); setRes(null)
    try {
      const r = await api.parkingCheck(p)
      const s = { lat: r.lat, lon: r.lon, label: label || r.address || ('q' in p ? p.q : `${r.lat.toFixed(3)}, ${r.lon.toFixed(3)}`) }
      setSpot(s); store.set(KEY, JSON.stringify(s)); setRes(r)
    } catch (e) { setErr(errText(e, t('p15.park.fail'))) }
    setBusy(false)
  }
  const download = () => {
    const blob = new Blob([moveCarIcs(t('p15.park.icsSum'), spot?.label ?? '')], { type: 'text/calendar' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'move-car.ics'; a.click()
    setTimeout(() => URL.revokeObjectURL(a.href), 2000)
  }
  // Localized via backend codes; falls back to the English text when a key is missing.
  const tr = (code: string | undefined, fb: string, vars?: Record<string, string | number>) => {
    if (!code) return fb
    const v = t(code)
    return v && v !== code ? fill(t, code, vars) : fb
  }
  const move = res?.verdict === 'move'
  return (
    <Card title={<span className="flex items-center gap-2"><Car aria-hidden size={18} className="text-brand" />{t('p15.park.title')}</span>} titleAs="h2" subtitle={t('p15.park.sub')}>
      {spot && <p className="mb-2 text-body-sm text-muted">{fill(t, 'p15.park.spot', { label: '\u2068' + spot.label + '\u2069' })}</p>}
      <div className="flex flex-wrap gap-2">
        {place && <Button variant="secondary" icon={MapPin} loading={busy} onClick={() => run({ lat: place.lat, lon: place.lon }, place.label)}>{t('p15.park.use')}</Button>}
        {spot && <Button variant="secondary" loading={busy} onClick={() => run({ lat: spot.lat, lon: spot.lon }, spot.label)}>{t('p15.park.check')}</Button>}
      </div>
      <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); if (addr.trim()) void run({ q: addr.trim() }) }}>
        <Input value={addr} onChange={(e) => setAddr(e.target.value)} placeholder={t('p15.park.addr')} aria-label={t('p15.park.addr')} maxLength={200} />
        <Button type="submit" loading={busy} disabled={!addr.trim()}>{t('p15.park.check')}</Button>
      </form>
      {busy && <div className="mt-3" aria-busy="true"><SkeletonText lines={2} /></div>}
      {err && <div className="mt-3"><ErrorBox error={err} /></div>}
      {res && (
        <div className={`mt-3 rounded-md border-s-4 p-3 ${move ? 'border-watch bg-surface-2' : 'border-line bg-surface-2'}`} role="status">
          <p className="text-body font-semibold text-ink">{tr(res.headline_code, res.headline)}</p>
          <p className="text-body-sm text-ink">{tr(res.detail_code, res.detail)}</p>
          {res.reasons?.length > 0 && <ul className="mt-2 list-disc ps-5 text-body-sm text-ink">{res.reasons.map((r) => <li key={r.code}>{tr('p30.park.reason.' + r.code, r.text, r.params)}</li>)}</ul>}
          {move && (
            <div className="mt-3 flex flex-wrap gap-2">
              {res.higher_ground?.maps_url && /^https:\/\//.test(res.higher_ground.maps_url) && (
                <ButtonLink href={res.higher_ground.maps_url} target="_blank" rel="noreferrer" size="sm">{t('p15.park.maps')}</ButtonLink>
              )}
              <Button size="sm" variant="secondary" icon={CalendarPlus} onClick={download}>{t('p15.park.ics')}</Button>
            </div>
          )}
          <p className="mt-2 text-caption text-muted">{tr(res.limits_code, res.limits || t('p15.park.limits'))}</p>
        </div>
      )}
      {spot && <Button className="mt-3" variant="ghost" size="sm" icon={Trash2} onClick={() => { setSpot(null); setRes(null); store.set(KEY, null) }}>{t('p15.park.clear')}</Button>}
    </Card>
  )
}
