import { Check, ChevronRight, type LucideIcon } from 'lucide-react'
import { useApp } from '../../ctx'

/** Whole-card link with icon tile, title, one-line why, and a separate "Mark done" button. */
export function ActionCard({ icon: Icon, title, why, href, onDone, done = false }: {
  icon: LucideIcon; title: string; why: string; href: string; onDone?: () => void; done?: boolean
}) {
  const { t } = useApp()
  return (
    <div className="flex items-stretch gap-1 rounded-lg border border-line bg-surface shadow-card">
      <a href={href} className="flex min-h-18 min-w-0 flex-1 items-center gap-3 rounded-lg p-3 hover:bg-surface-2/60">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-brand-tint text-brand"><Icon aria-hidden size={20} /></span>
        <span className="min-w-0 flex-1">
          <span className={`block text-h3 ${done ? 'text-muted line-through' : 'text-ink'}`}>{title}</span>
          <span className="block text-body-sm text-muted">{why}</span>
        </span>
        <ChevronRight aria-hidden size={20} className="shrink-0 text-muted rtl:rotate-180" />
      </a>
      {onDone && (
        <button type="button" onClick={onDone} aria-pressed={done} aria-label={`${t('ds.markDone')}: ${title}`} title={t('ds.markDone')}
          className={`m-2 ms-0 inline-flex size-11 shrink-0 items-center justify-center self-center rounded-full border ${done ? 'border-normal bg-normal-tint text-normal' : 'border-ui text-muted hover:text-ink'}`}>
          <Check aria-hidden size={20} />
        </button>
      )}
    </div>
  )
}
