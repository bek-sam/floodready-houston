import type { ElementType, ReactNode } from 'react'
import { LEVEL_CLASS, type Level } from '../../lib/levels'

export type CardTone = 'default' | 'inset' | Level

/** Card: bg-surface, border-line, radius-lg, shadow-card. `tone=<level>` adds a 4px top border in that color. */
export function Card({ title, subtitle, action, tone = 'default', padding = 'md', as: As = 'section', className = '', id, children, titleAs: H = 'h2', ...rest }: {
  title?: ReactNode; subtitle?: ReactNode; action?: ReactNode; tone?: CardTone; padding?: 'md' | 'lg'
  as?: ElementType; titleAs?: ElementType; className?: string; id?: string; children?: ReactNode
  'aria-labelledby'?: string; 'aria-busy'?: boolean
}) {
  const base = tone === 'inset' ? 'bg-surface-2 border border-transparent' : 'bg-surface border border-line shadow-card'
  const top = tone !== 'default' && tone !== 'inset' ? `border-t-4 ${LEVEL_CLASS[tone].borderTop}` : ''
  const pad = padding === 'lg' ? 'p-5 md:p-6' : 'p-4'
  return (
    <As id={id} className={`rounded-lg ${base} ${top} ${pad} ${className}`} {...rest}>
      {(title || action) && (
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            {title && <H className="text-h3 text-ink">{title}</H>}
            {subtitle && <p className="mt-0.5 text-body-sm text-muted">{subtitle}</p>}
          </div>
          {action && <div className="-my-1.5 shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </As>
  )
}
