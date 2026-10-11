import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

/** Centered empty state: icon in a 64px circle, h3 title, short body, one action. */
export function EmptyState({ icon: Icon, title, body, action, secondary, className = '' }: {
  icon: LucideIcon; title: ReactNode; body?: ReactNode; action?: ReactNode; secondary?: ReactNode; className?: string
}) {
  return (
    <div className={`flex flex-col items-center px-4 py-8 text-center ${className}`}>
      <span className="mb-3 flex size-16 items-center justify-center rounded-full bg-surface-2 text-brand">
        <Icon aria-hidden size={32} />
      </span>
      <h2 className="text-h3 text-ink">{title}</h2>
      {body && <p className="mt-1 max-w-[40ch] text-body-sm text-muted">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
      {secondary && <div className="mt-2">{secondary}</div>}
    </div>
  )
}
