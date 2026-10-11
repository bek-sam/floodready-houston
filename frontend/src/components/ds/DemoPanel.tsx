import type { ReactNode } from 'react'
import { FlaskConical } from 'lucide-react'
import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'

/** Demo-only controls. Renders nothing unless demo mode is on. */
export function DemoPanel({ title, children, className = '', id }: { title?: ReactNode; children: ReactNode; className?: string; id?: string }) {
  const { demo } = useDemoMode()
  const { t } = useApp()
  if (!demo) return null
  return (
    <section id={id} className={`rounded-lg border-[1.5px] border-dashed border-watch bg-watch-tint p-4 ${className}`}>
      <p className="mb-2 flex items-center gap-1.5 text-overline uppercase text-watch"><FlaskConical aria-hidden size={14} />{t('demo.panel')}</p>
      {title && <h2 className="mb-2 text-h3 text-ink">{title}</h2>}
      {children}
    </section>
  )
}
