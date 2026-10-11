import { useCallback, useEffect, useState } from 'react'
import { BellRing, Info } from 'lucide-react'
import { api, errText } from '../api'
import { useApp } from '../ctx'
import { Card, ErrorBox, Switch } from './ds'

const b64 = (s: string) => {
  const raw = atob((s + '='.repeat((4 - (s.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/'))
  return Uint8Array.from(raw, (c) => c.charCodeAt(0))
}
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent)
const standalone = window.matchMedia('(display-mode: standalone)').matches || (navigator as unknown as { standalone?: boolean }).standalone === true
const INAPP = 'floodready.inappAlerts'
const getFlag = () => { try { return localStorage.getItem(INAPP) === '1' } catch { return false } }
const setFlag = (on: boolean) => { try { if (on) localStorage.setItem(INAPP, '1'); else localStorage.removeItem(INAPP) } catch { /* ignore */ } }

export type PushState = 'off' | 'on' | 'blocked' | 'unsupported'

/** One alerts switch: Web Push when the browser supports it, otherwise in-app Notification permission. */
export function usePush(placeIds: string[]) {
  const { t, lang } = useApp()
  const pushOk = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
  const notifOk = 'Notification' in window
  const [sub, setSub] = useState<PushSubscription | null>(null)
  const [perm, setPerm] = useState<string>(() => (notifOk ? Notification.permission : 'unsupported'))
  const [inapp, setInapp] = useState(getFlag)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const ids = placeIds.join(',')

  useEffect(() => {
    if (!pushOk) return
    navigator.serviceWorker.getRegistration().then((r) => r?.pushManager.getSubscription()).then((s) => setSub(s ?? null)).catch(() => {})
  }, [pushOk])

  // keep the server's list of watched places in step with this phone's subscription
  useEffect(() => {
    if (sub && ids) api.pushSubscribe(sub.toJSON(), ids.split(','), lang).catch(() => {})
  }, [sub, ids, lang])

  const state: PushState = !notifOk ? 'unsupported' : perm === 'denied' ? 'blocked' : (pushOk ? !!sub : inapp && perm === 'granted') ? 'on' : 'off'

  const enable = useCallback(async () => {
    setBusy(true); setErr(null)
    try {
      const p = await Notification.requestPermission(); setPerm(p)
      if (p !== 'granted') return
      if (!pushOk) { setFlag(true); setInapp(true); return }
      try {
        const reg = (await navigator.serviceWorker.getRegistration()) ?? (await navigator.serviceWorker.register('/sw.js'))
        await navigator.serviceWorker.ready
        const { key } = await api.vapidKey()
        const s = (await reg.pushManager.getSubscription()) ?? (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64(key) }))
        await api.pushSubscribe(s.toJSON(), ids ? ids.split(',') : [], lang)
        setSub(s)
      } catch (e) { setFlag(true); setInapp(true); setErr(errText(e, t('p3.sw.noKey'))) }
    } finally { setBusy(false) }
  }, [pushOk, ids, lang, t])

  const disable = useCallback(async () => {
    setBusy(true); setErr(null)
    try {
      if (sub) { await api.pushUnsubscribe(sub.endpoint).catch(() => {}); await sub.unsubscribe().catch(() => {}); setSub(null) }
      setFlag(false); setInapp(false)
    } finally { setBusy(false) }
  }, [sub])

  const send = useCallback(async (kind: 'test' | 'sim') => {
    if (!sub) return null
    setBusy(true); setErr(null)
    try { return (kind === 'test' ? await api.pushTest(sub.endpoint) : await api.pushSimulate(sub.endpoint)).sent }
    catch (e) { setErr(errText(e, t('offline'))); return null } finally { setBusy(false) }
  }, [sub, t])

  return { state, sub, busy, err, enable, disable, send, pushOk, count: placeIds.length }
}
export type PushApi = ReturnType<typeof usePush>

/** "Alerts on this phone" card: a single switch replaces the old three push/notification buttons. */
export default function AlertsSwitch({ push }: { push: PushApi }) {
  const { t } = useApp()
  const { state, busy, err, enable, disable, count, pushOk } = push
  const sub = state === 'on'
    ? (pushOk ? (count === 1 ? t('p3.sw.onFor1') : t('p3.sw.onFor').replace('{n}', String(count))) : t('p3.sw.inapp'))
    : state === 'blocked' ? t('p3.sw.blocked') : state === 'unsupported' ? t('p3.sw.unsupported') : t('p3.sw.sub')
  return (
    <Card>
      <div className="flex items-start gap-3">
        <BellRing aria-hidden size={24} className="mt-3 shrink-0 text-brand" />
        <div className="min-w-0 flex-1">
          <Switch label={t('p3.sw.label')} description={sub} checked={state === 'on'} disabled={busy || state === 'blocked' || state === 'unsupported'}
            onChange={(v) => { void (v ? enable() : disable()) }} />
        </div>
      </div>
      {isIOS && !standalone && (
        <p className="mt-3 flex items-start gap-2 rounded-md bg-brand-tint p-3 text-body-sm text-ink">
          <Info aria-hidden size={18} className="mt-0.5 shrink-0 text-brand" />{t('p3.sw.ios')}
        </p>
      )}
      {err && <ErrorBox className="mt-3" error={err} />}
      <p className="mt-3 text-caption text-muted">{t('p3.sw.foot')}</p>
    </Card>
  )
}
