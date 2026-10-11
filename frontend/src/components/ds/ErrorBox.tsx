import { TriangleAlert, RefreshCw } from 'lucide-react'
import { useApp } from '../../ctx'
import { Button } from './Button'

/** Inline error: danger-tint bg, plain message, optional "Try again". */
export function ErrorBox({ error, onRetry, className = '' }: { error: string; onRetry?: () => void; className?: string }) {
  const { t } = useApp()
  return (
    <div role="alert" className={`flex items-start gap-3 rounded-md border border-danger bg-danger-tint p-3 text-body-sm text-ink ${className}`}>
      <TriangleAlert aria-hidden size={20} className="mt-0.5 shrink-0 text-danger" />
      <div className="min-w-0 flex-1">
        <p>{error}</p>
        {onRetry && <Button variant="secondary" size="sm" icon={RefreshCw} className="mt-2" onClick={onRetry}>{t('retry')}</Button>}
      </div>
    </div>
  )
}
