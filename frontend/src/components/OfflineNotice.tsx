import { WifiOff } from 'lucide-react'
import { useApp } from '../ctx'
import { fmtAt, lastHomeAt } from '../lib/offline'

/** Clear offline state for pages that need the server: last update time, what still works, link to the safety card. */
export default function OfflineNotice({ at }: { at?: number | null }) {
  const { t, lang } = useApp()
  const ts = at === undefined ? lastHomeAt() : at
  return (
    <div role="status" className="rounded-md border border-line bg-surface-2 p-3 text-body-sm text-ink">
      <p className="flex items-start gap-2 font-semibold">
        <WifiOff aria-hidden size={18} className="mt-0.5 shrink-0 text-muted" />
        <span>{ts ? t('p37.off.title').replace('{time}', fmtAt(ts, lang)) : t('p37.off.none')}</span>
      </p>
      <p className="mt-1 text-muted">{t('p37.off.works')}</p>
      <a href="#offline" className="mt-2 inline-flex min-h-11 items-center font-semibold text-brand underline underline-offset-2">{t('p37.off.link')}</a>
    </div>
  )
}
