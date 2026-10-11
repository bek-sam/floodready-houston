import { WifiOff } from 'lucide-react'
import { useApp } from '../../ctx'

export function OfflineBanner() {
  const { t } = useApp()
  return (
    <div role="status" className="flex items-center justify-center gap-2 border-b border-line bg-surface-2 px-4 py-2 text-body-sm text-ink md:justify-start md:px-6">
      <WifiOff aria-hidden size={16} className="shrink-0 text-muted" />
      <span>{t('shell.offline')}</span>
    </div>
  )
}
