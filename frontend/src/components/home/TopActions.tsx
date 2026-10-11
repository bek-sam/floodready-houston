import { useEffect, useState } from 'react'
import { Accessibility, BellRing, ClipboardList, FileText, HeartPulse, Mail, MessageCircleQuestion, Route, type LucideIcon } from 'lucide-react'
import { useApp } from '../../ctx'
import { easyT, useEasy } from '../easyread/easyRead'
import { LEVEL_RANK, type Exposure, type Level } from '../../lib/levels'
import { ACTION_HREF, fill, medicalKind, topActions, type ActionId } from '../../lib/summary'
import { KEYS, store, usePlace } from '../../state/place'
import { ActionCard, Disclosure, LoadingText, Skeleton, toast } from '../ds'

const ICON: Record<ActionId, LucideIcon> = {
  drive: Route, alerts: BellRing, medical: HeartPulse, evac: Accessibility, insurance: FileText,
  renter: Mail, plan: ClipboardList, ask: MessageCircleQuestion,
}

const id_evacNow = (now: Level) => LEVEL_RANK[now] >= LEVEL_RANK.warning

/** True when this browser already has a push subscription (alerts are on). */
function useHasPush(): boolean | null {
  const [has, setHas] = useState<boolean | null>(null)
  useEffect(() => {
    let live = true
    const done = (v: boolean) => { if (live) setHas(v) }
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) { done(false); return }
      navigator.serviceWorker.getRegistration()
        .then((reg) => (reg ? reg.pushManager.getSubscription() : null))
        .then((s) => done(!!s))
        .catch(() => done(false))
    } catch { done(false) }
    return () => { live = false }
  }, [])
  return has
}

const loadDone = (): Record<string, string> => {
  const v = store.json<Record<string, string>>(KEYS.actionsDone, {})
  return v && typeof v === 'object' ? v : {}
}

/** "Do these 3 things now" (§4.4). Waits for the levels so cards don't jump. */
export function TopActions({ placeLabel, now, exposure, ready }: { placeLabel: string; now: Level; exposure: Exposure; ready: boolean }) {
  const { t: t0 } = useApp()
  const [easy] = useEasy(); const t = (k: string) => easyT(t0, k, easy)
  const { household, place } = usePlace()
  const hasPush = useHasPush()
  const [done, setDone] = useState(loadDone)
  const hasPlan = !!store.get('lastPlan') && store.get('lastPlan') !== 'null'
  const save = (d: Record<string, string>) => { setDone(d); store.set(KEYS.actionsDone, JSON.stringify(d)) }
  const loading = !ready || hasPush === null
  const list = topActions({ now, exposure, household, hasPush: !!hasPush, hasPlan, done, placeSavedAt: place?.savedAt ?? null })

  const help = id_evacNow(now)
  const title = (id: ActionId) => id === 'evac' && help ? t('p39.evac.t') : id === 'alerts' ? fill(t, 'act.alerts.t', { place: placeLabel })
    : id === 'medical' ? fill(t, 'act.medical.t', { what: '@act.medical.' + medicalKind(household) }) : t(`act.${id}.t`)
  const mark = (id: ActionId) => {
    const prev = done
    save({ ...done, [id]: new Date().toISOString() })
    toast({ message: t('act.marked'), action: { label: t('act.undo'), onClick: () => save(prev) } })
  }
  const unmark = (id: ActionId) => { const n = { ...done }; delete n[id]; save(n) }

  return (
    <section aria-labelledby="act-title" aria-busy={loading || undefined}>
      <h2 id="act-title" className="text-h2 text-ink">{t('act.title')}</h2>
      <p className="mt-0.5 hidden text-body-sm text-muted sm:block">{fill(t, 'act.sub', { place: placeLabel })}</p>
      <div className="mt-3 space-y-3">
        {loading ? (
          <>
            <LoadingText />
            {[0, 1, 2].map((i) => (
              <div key={i} aria-hidden className="flex min-h-18 items-center gap-3 rounded-lg border border-line bg-surface p-3 shadow-card">
                <Skeleton w={40} h={40} radius={12} />
                <span className="flex flex-1 flex-col gap-2"><Skeleton w="70%" h={18} /><Skeleton w="90%" h={14} /></span>
              </div>
            ))}
          </>
        ) : (
          <ul className="space-y-3">
            {list.active.map((id) => (
              <li key={id}><ActionCard icon={ICON[id]} title={title(id)} why={id === 'evac' && help ? t('p39.evac.w') : t(`act.${id}.w`)} href={ACTION_HREF[id]} onDone={() => mark(id)} /></li>
            ))}
          </ul>
        )}
        {!loading && list.done.length > 0 && (
          <Disclosure title={fill(t, 'act.done', { n: list.done.length })}>
            <ul className="space-y-3">
              {list.done.map((id) => (
                <li key={id}><ActionCard icon={ICON[id]} title={title(id)} why={id === 'evac' && help ? t('p39.evac.w') : t(`act.${id}.w`)} href={ACTION_HREF[id]} done onDone={() => unmark(id)} /></li>
              ))}
            </ul>
          </Disclosure>
        )}
      </div>
    </section>
  )
}
