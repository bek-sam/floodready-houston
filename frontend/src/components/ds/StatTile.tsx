import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { LEVEL_CLASS, type Level } from '../../lib/levels'

/** Compact metric tile: overline label, 22px value, optional sub line and source. */
export function StatTile({ label, value, sub, icon: Icon, level, source, className = '' }: {
  label: ReactNode; value: ReactNode; sub?: ReactNode; icon?: LucideIcon; level?: Level; source?: ReactNode; className?: string
}) {
  return (
    <div className={`min-h-22 rounded-md bg-surface-2 p-4 ${className}`}>
      <p className="flex items-center gap-1.5 text-overline uppercase text-muted">
        {Icon && <Icon aria-hidden size={14} className={level ? LEVEL_CLASS[level].text : ''} />}{label}
      </p>
      <p className={`mt-1 text-[22px] font-semibold leading-7 tabular-nums ${level ? LEVEL_CLASS[level].text : 'text-ink'}`}>{value}</p>
      {sub && <p className="mt-0.5 text-body-sm text-muted">{sub}</p>}
      {source && <p className="mt-1">{source}</p>}
    </div>
  )
}
