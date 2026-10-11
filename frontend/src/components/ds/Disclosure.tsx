import { useEffect, useId, useState, type ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

const hashTargets = (id: string) => {
  const h = decodeURIComponent(location.hash.slice(1))
  return h === id || h.split('/').slice(1).includes(id)
}

/** 56px row button with aria-expanded and a region. Opens itself when the URL hash targets `id` (e.g. #home/rentbuy). */
export function Disclosure({ title, preview, defaultOpen = false, id, icon, children, className = '' }: {
  title: ReactNode; preview?: ReactNode; defaultOpen?: boolean; id?: string; icon?: ReactNode; children: ReactNode; className?: string
}) {
  const auto = useId()
  const rid = id ?? 'd' + auto.replace(/:/g, '')
  const [open, setOpen] = useState(() => defaultOpen || (id ? hashTargets(id) : false))
  useEffect(() => {
    if (!id) return
    const f = () => { if (hashTargets(id)) { setOpen(true); requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ block: 'start' })) } }
    f()
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [id])
  return (
    <div id={id} className={`rounded-lg border border-line bg-surface shadow-card ${className}`}>
      <button type="button" aria-expanded={open} aria-controls={rid + '-region'} onClick={() => setOpen(!open)}
        className="flex min-h-14 w-full items-center gap-3 rounded-lg px-4 py-2 text-start hover:bg-surface-2/60">
        {icon && <span aria-hidden className="shrink-0 text-brand">{icon}</span>}
        <span className="min-w-0 flex-1">
          <span className="block text-h3 text-ink">{title}</span>
          {preview && !open && <span className="block truncate text-caption text-muted">{preview}</span>}
        </span>
        <ChevronDown aria-hidden size={20} className={`shrink-0 text-muted transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div id={rid + '-region'} role="region" aria-label={typeof title === 'string' ? title : undefined} className="fr-fade-in border-t border-line px-4 py-4">{children}</div>}
    </div>
  )
}
