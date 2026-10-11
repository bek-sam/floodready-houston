// Legacy component API kept for pages not yet migrated. These are thin wrappers over the
// design system in ./ds — new code should import from './ds' directly. Removed in P6.
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Info } from 'lucide-react'
import { errText, type Status } from '../api'
import { useApp } from '../ctx'
import { Button, Card as DsCard, ErrorBox as DsErrorBox, Field as DsField, LoadingText, SkeletonText, SourceLink, StatusBadge, inputCls as dsInputCls } from './ds'

export function Card({ title, children, className = '' }: { title?: ReactNode; children: ReactNode; className?: string }) {
  return <DsCard title={title} titleAs="h2" className={className}>{children}</DsCard>
}

export function Btn({ variant = 'primary', className = '', ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' }) {
  return <Button variant={variant === 'primary' ? 'primary' : 'secondary'} className={className} {...p} />
}

export const inputCls = dsInputCls

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <DsField label={label}>{children}</DsField>
}

export function ErrorBox({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return <DsErrorBox error={error} onRetry={onRetry} />
}

export function Loading() {
  return <div aria-busy="true" className="py-2"><LoadingText /><SkeletonText lines={3} /></div>
}

export function SrcLink({ href, label }: { href: string; label?: string }) {
  return <SourceLink href={href} label={label} />
}

const STATUS_VAR: Record<Status, string> = {
  normal: 'var(--s-normal)', action: 'var(--s-action)', minor: 'var(--s-minor)',
  moderate: 'var(--s-moderate)', major: 'var(--s-major)', unknown: 'var(--s-unknown)',
}
export const statusColor = (s: Status) => STATUS_VAR[s] ?? STATUS_VAR.unknown

export function StatusChip({ status }: { status: Status }) {
  return <StatusBadge status={status} />
}

/** Run an async loader with loading/error state. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[], enabled = true) {
  const { t } = useApp()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(enabled)
  const [n, setN] = useState(0)
  useEffect(() => {
    if (!enabled) return
    let live = true
    setLoading(true); setError(null)
    fn().then((d) => { if (live) setData(d) })
      .catch((e) => { if (live) setError(errText(e, t('offline'))) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled, n])
  const reload = useCallback(() => setN((x) => x + 1), [])
  return { data, error, loading, reload }
}

/** Leaflet needs real colors, not CSS variables. */
export function mapColor(s: Status): string {
  const name = (STATUS_VAR[s] ?? STATUS_VAR.unknown).replace(/^var\(|\)$/g, '')
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  // Legacy aliases are themselves var() references; resolve one level more.
  const m = v.match(/^var\((--[\w-]+)\)$/)
  return (m ? getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim() : v) || '#4A5868'
}

/** Subtle note for backend `warnings: []` (partial/fallback data). */
export function Warnings({ items }: { items?: string[] }) {
  if (!Array.isArray(items) || !items.length) return null
  return (
    <p className="flex items-start gap-1.5 text-caption text-muted">
      <Info aria-hidden size={14} className="mt-0.5 shrink-0" />{items.join(' · ')}
    </p>
  )
}
