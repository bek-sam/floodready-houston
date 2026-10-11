import { Phone } from 'lucide-react'
import { useApp } from '../../ctx'

/** Always-on 911 strip. Calm (inverse) by default; red with role=alert only when Right now = Danger. */
export function EmergencyStrip({ dangerEvent, placeName }: { dangerEvent: string | null; placeName?: string }) {
  const { t } = useApp()
  if (dangerEvent) {
    return (
      <div role="alert" className="bg-danger text-white dark:text-bg">
        <a href="tel:911" className="flex min-h-11 items-center justify-center gap-2 px-4 py-2 text-center text-body-sm font-semibold md:justify-start">
          <Phone aria-hidden size={16} className="shrink-0" />
          <span>{t('strip.danger').replace('{event}', dangerEvent).replace('{place}', placeName ?? '')}</span>
        </a>
      </div>
    )
  }
  return (
    <div className="bg-strip text-stripink">
      <a href="tel:911" className="flex min-h-11 items-center justify-center gap-2 px-4 text-body-sm md:justify-start md:px-6">
        <Phone aria-hidden size={16} className="shrink-0" />
        <span>{t('strip.lead')} <b className="font-bold underline underline-offset-2">{t('strip.call')}</b></span>
        <span aria-hidden className="hidden opacity-60 md:inline">|</span>
        <span className="hidden opacity-80 md:inline">{t('strip.notOfficial')}</span>
      </a>
    </div>
  )
}
