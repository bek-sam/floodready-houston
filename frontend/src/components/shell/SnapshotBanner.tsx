import { useSyncExternalStore } from 'react'
import { DatabaseZap } from 'lucide-react'
import { useApp } from '../../ctx'
import { getSnapshot, subscribeSnapshot } from '../../lib/snapshot'

export function SnapshotBanner() {
  const { t, lang } = useApp()
  const snap = useSyncExternalStore(subscribeSnapshot, getSnapshot)
  if (!snap) return null
  let time = ''
  if (snap.date) { try { time = new Date(snap.date).toLocaleString(lang, { dateStyle: 'medium', timeStyle: 'short' }) } catch { time = snap.date } }
  return (
    <div role="status" className="flex items-center justify-center gap-2 border-b border-line bg-surface-2 px-4 py-1.5 text-body-sm text-ink md:justify-start md:px-6">
      <DatabaseZap aria-hidden size={16} className="shrink-0 text-muted" />
      <span>{t('p14.banner').replace('{time}', time || '—')}</span>
    </div>
  )
}
