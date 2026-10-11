import type { ReactNode } from 'react'
import { MapPin } from 'lucide-react'
import { useApp } from '../../ctx'
import { usePlace, placeName, streetOf } from '../../state/place'
import { useShell } from '../shell/ShellContext'

/** Page title (h1) + optional subtitle + optional right-side action. */
export function PageHeader({ title, subtitle, action, forPlace = false }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode; forPlace?: boolean }) {
  return (
    <header className="mb-6">
      <div className="flex items-start justify-between gap-3">
        <h1 className="text-h1 text-ink">{title}</h1>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {subtitle && <p className="mt-1 text-body-sm text-muted">{subtitle}</p>}
      {forPlace && <ForPlace className="mt-2" />}
    </header>
  )
}

/** "For: Home · 5300 N Braeswood Blvd · Change" line. Change opens the My place sheet. */
export function ForPlace({ className = '' }: { className?: string }) {
  const { t } = useApp()
  const { place } = usePlace()
  const { openPlaceSheet } = useShell()
  return (
    <p className={`flex flex-wrap items-center gap-x-1.5 text-caption text-muted ${className}`}>
      <MapPin aria-hidden size={14} />
      {place ? <span>{t('place.for')}: {placeName(place.nickname, t)} · {streetOf(place.label)}</span> : <span>{t('place.none')}</span>}
      <span aria-hidden>·</span>
      <button type="button" onClick={openPlaceSheet} className="min-h-6 font-semibold text-brand underline underline-offset-2">
        {place ? t('place.change') : t('place.set')}
      </button>
    </p>
  )
}
