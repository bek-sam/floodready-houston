import { useRef, type ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { rovingIndex } from './keys'

export interface SegOption<V extends string = string> { value: V; label: ReactNode; icon?: LucideIcon }

/** Segmented control (role=radiogroup). 44px tall; md is full width with equal segments. */
export function Segmented<V extends string>({ options, value, onChange, label, size = 'md', className = '' }: {
  options: SegOption<V>[]; value: V | null; onChange: (v: V) => void; label: string; size?: 'sm' | 'md'; className?: string
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const focusIdx = Math.max(0, options.findIndex((o) => o.value === value))
  return (
    <div role="radiogroup" aria-label={label}
      className={`${size === 'md' ? 'flex w-full' : 'inline-flex'} gap-1 rounded-md bg-surface-2 p-1 ${className}`}>
      {options.map((o, i) => {
        const sel = o.value === value
        const Icon = o.icon
        return (
          <button key={o.value} ref={(el) => { refs.current[i] = el }} type="button" role="radio" aria-checked={sel}
            tabIndex={i === focusIdx ? 0 : -1} onClick={() => onChange(o.value)}
            onKeyDown={(e) => { const n = rovingIndex(e, i, options.length); if (n !== null) { e.preventDefault(); onChange(options[n].value); refs.current[n]?.focus() } }}
            className={`inline-flex min-h-9 flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-sm px-3 text-body-sm font-semibold transition-colors duration-150 ${sel ? 'bg-surface text-ink shadow-card ring-1 ring-line' : 'text-muted hover:text-ink'}`}>
            {Icon && <Icon aria-hidden size={16} />}{o.label}
          </button>
        )
      })}
    </div>
  )
}
