import { useRef, type ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { rovingIndex } from './keys'

export interface TabItem<V extends string = string> { value: V; label: ReactNode; icon?: LucideIcon }

/** Underline tabs, 44px, role=tablist with arrow-key navigation. Panels: give them id `${idPrefix}-panel-${value}`. */
export function Tabs<V extends string>({ items, value, onChange, label, idPrefix = 'tabs', className = '' }: {
  items: TabItem<V>[]; value: V; onChange: (v: V) => void; label: string; idPrefix?: string; className?: string
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  return (
    <div role="tablist" aria-label={label} className={`flex gap-1 overflow-x-auto border-b border-line [scrollbar-width:none] ${className}`}>
      {items.map((it, i) => {
        const sel = it.value === value
        const Icon = it.icon
        return (
          <button key={it.value} ref={(el) => { refs.current[i] = el }} type="button" role="tab" id={`${idPrefix}-tab-${it.value}`}
            aria-selected={sel} aria-controls={`${idPrefix}-panel-${it.value}`} tabIndex={sel ? 0 : -1}
            onClick={() => onChange(it.value)}
            onKeyDown={(e) => { const n = rovingIndex(e, i, items.length); if (n !== null) { e.preventDefault(); onChange(items[n].value); refs.current[n]?.focus() } }}
            className={`-mb-px inline-flex min-h-11 shrink-0 items-center gap-2 whitespace-nowrap border-b-2 px-3 text-body-sm font-semibold transition-colors duration-150 ${sel ? 'border-brand text-brand' : 'border-transparent text-muted hover:text-ink'}`}>
            {Icon && <Icon aria-hidden size={18} />}{it.label}
          </button>
        )
      })}
    </div>
  )
}
