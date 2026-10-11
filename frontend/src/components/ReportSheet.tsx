import { useState } from 'react'
import { LocateFixed } from 'lucide-react'
import { api, errText, type LatLon, type Report } from '../api'
import { HOUSTON, useApp } from '../ctx'
import { streetOf, usePlace } from '../state/place'
import { Button, ErrorBox, Field, Select, Sheet, inputCls, toast } from './ds'

const KINDS = ['flooded_road', 'water_over_road', 'barricade_missing', 'stalled_vehicles', 'other']

/** "Report flooding" form in a Sheet. Used by Drive, Alerts and (P5) Recover. Posts to /reports at My place or the current GPS fix. */
export default function ReportSheet({ open, onClose, onSent }: { open: boolean; onClose: () => void; onSent?: () => void }) {
  const { t } = useApp()
  const { place } = usePlace()
  const [kind, setKind] = useState(KINDS[0])
  const [depth, setDepth] = useState('')
  const [note, setNote] = useState('')
  const [gps, setGps] = useState<LatLon | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const loc: LatLon = gps ?? place ?? HOUSTON
  const useGps = () => {
    try {
      navigator.geolocation.getCurrentPosition(
        (p) => setGps({ lat: p.coords.latitude, lon: p.coords.longitude }),
        () => setErr(t('p3.drive.locFail')), { enableHighAccuracy: true, timeout: 10000 })
    } catch { setErr(t('p3.drive.locFail')) }
  }
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr(null)
    const r: Report = { lat: loc.lat, lon: loc.lon, kind, depth_in: depth ? +depth : null, note }
    try {
      await api.postReport(r)
      setNote(''); setDepth(''); setGps(null)
      toast(t('p3.rs.sent')); onSent?.(); onClose()
    } catch (e2) { setErr(errText(e2, t('offline'))) } finally { setBusy(false) }
  }

  return (
    <Sheet open={open} onClose={onClose} title={t('p3.rs.title')}>
      <form onSubmit={submit} className="space-y-4">
        <Field label={t('p3.rs.kind')}>
          <Select value={kind} onChange={(e) => setKind(e.target.value)}>
            {KINDS.map((k) => <option key={k} value={k}>{t('c6.kind.' + k)}</option>)}
          </Select>
        </Field>
        <Field label={t('p3.rs.depth')}><input type="number" inputMode="numeric" min={0} className={inputCls} value={depth} onChange={(e) => setDepth(e.target.value)} /></Field>
        <Field label={t('p3.rs.note')}><textarea className={inputCls} rows={2} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} /></Field>
        <div className="rounded-md bg-surface-2 p-3">
          <p className="text-caption font-semibold text-ink">{t('p3.rs.where')}</p>
          <p className="text-body-sm text-muted">
            {gps ? t('p3.rs.gpsOn') : place ? t('p3.rs.atPlace').replace('{street}', streetOf(place.label)) : t('p3.rs.atHouston')}
          </p>
          {!gps && <Button variant="ghost" size="sm" icon={LocateFixed} className="-ms-3 mt-1" onClick={useGps}>{t('p3.rs.useGps')}</Button>}
        </div>
        {err && <ErrorBox error={err} />}
        <Button type="submit" size="lg" full loading={busy}>{t('p3.rs.submit')}</Button>
        <p className="text-caption text-muted">{t('p3.rs.unverified')}</p>
      </form>
    </Sheet>
  )
}
