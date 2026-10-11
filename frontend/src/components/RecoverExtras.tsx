import { useState } from 'react'
import { Copy, LocateFixed, Phone } from 'lucide-react'
import { useApp } from '../ctx'
import { Button, ButtonLink, Card, Checkbox, Input } from './ds'

const ITEMS = ['photos', 'receipts', 'femaNum', 'claim', 'mold']
const KEY = 'recoveryTracker'
const load = (): { done: Record<string, boolean>; fema: string } => {
  try { const v = JSON.parse(localStorage.getItem(KEY) || '{}'); return { done: v.done ?? {}, fema: v.fema ?? '' } } catch { return { done: {}, fema: '' } }
}

export function RecoveryTracker() {
  const { t } = useApp()
  const [st, setSt] = useState(load)
  const save = (n: typeof st) => { setSt(n); try { localStorage.setItem(KEY, JSON.stringify(n)) } catch { /* ignore */ } }
  const n = ITEMS.filter((k) => st.done[k]).length
  return (
    <Card title={t('p5.rec.trkTitle')} subtitle={<span aria-live="polite">{t('rec.done').replace('{n}', String(n)).replace('{m}', String(ITEMS.length))}</span>}>
      <div className="mb-2 h-2 w-full overflow-hidden rounded-full bg-surface-2" aria-hidden>
        <div className="h-full rounded-full bg-normal transition-all" style={{ width: `${(n / ITEMS.length) * 100}%` }} />
      </div>
      <ul>
        {ITEMS.map((k) => (
          <li key={k}>
            <Checkbox label={<span className={st.done[k] ? 'text-muted line-through' : ''}>{t('c5.trk.' + k)}</span>} checked={!!st.done[k]}
              onChange={(v) => save({ ...st, done: { ...st.done, [k]: v } })} />
          </li>
        ))}
      </ul>
      <label className="mt-3 block text-body-sm font-medium text-ink">{t('c5.trk.femaLabel')}
        <Input className="mt-1" inputMode="numeric" value={st.fema} onChange={(e) => save({ ...st, fema: e.target.value })} />
      </label>
      <p className="mt-2 text-caption text-muted">{t('c5.trk.local')}</p>
    </Card>
  )
}

export function Share911() {
  const { t } = useApp()
  const [pos, setPos] = useState<{ lat: number; lon: number; acc: number } | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const get = () => {
    setErr(null); setCopied(false)
    if (!navigator.geolocation) { setErr(t('c5.911.nogeo')); return }
    navigator.geolocation.getCurrentPosition(
      (p) => setPos({ lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy }),
      () => setErr(t('c5.911.denied')), { enableHighAccuracy: true, timeout: 15000 })
  }
  const text = pos ? `${pos.lat.toFixed(5)}, ${pos.lon.toFixed(5)}` : ''
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true) } catch { setErr(t('c5.911.copyFail')) }
  }
  return (
    <Card title={t('c5.911.title')} tone="inset">
      <p className="text-body-sm text-ink">{t('c5.911.intro')}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button icon={LocateFixed} onClick={get}>{t('c5.911.get')}</Button>
        <ButtonLink variant="danger" icon={Phone} href="tel:911">{t('sos')}</ButtonLink>
      </div>
      {err && <p className="mt-2 text-body-sm text-danger" role="alert">{err}</p>}
      {pos && (
        <div className="mt-3 text-body-sm" role="status">
          <p className="text-h2 text-ink">{text}</p>
          <p className="text-muted">{t('c5.911.acc').replace('{m}', String(Math.round(pos.acc)))} {t('c5.911.noAddr')}</p>
          <Button variant="secondary" icon={Copy} className="mt-2" onClick={copy}>{copied ? t('c5.911.copied') : t('c5.911.copy')}</Button>
        </div>
      )}
    </Card>
  )
}
