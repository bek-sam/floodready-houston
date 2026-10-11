import { useApp } from '../../ctx'

type Len = number | string
const px = (v: Len) => (typeof v === 'number' ? `${v}px` : v)

/** Placeholder block. aria-hidden; the parent sets aria-busy and can include <LoadingText/>. */
export function Skeleton({ w = '100%', h = 16, radius = 8, className = '' }: { w?: Len; h?: Len; radius?: Len; className?: string }) {
  return <span aria-hidden className={`fr-skeleton block ${className}`} style={{ width: px(w), height: px(h), borderRadius: px(radius) }} />
}
export function SkeletonText({ lines = 3, className = '' }: { lines?: number; className?: string }) {
  return (
    <span aria-hidden className={`flex flex-col gap-2 ${className}`}>
      {Array.from({ length: lines }, (_, i) => <Skeleton key={i} h={14} w={i === lines - 1 && lines > 1 ? '60%' : '100%'} />)}
    </span>
  )
}
/** sr-only "Loading" for a busy region. */
export function LoadingText({ label }: { label?: string }) {
  const { t } = useApp()
  return <span role="status" className="sr-only">{label ?? t('loading')}</span>
}
/** A card-shaped skeleton (title + lines). */
export function SkeletonCard({ lines = 3, className = '' }: { lines?: number; className?: string }) {
  return (
    <div aria-busy="true" className={`rounded-lg border border-line bg-surface p-4 shadow-card ${className}`}>
      <LoadingText />
      <Skeleton w="40%" h={20} className="mb-3" />
      <SkeletonText lines={lines} />
    </div>
  )
}
