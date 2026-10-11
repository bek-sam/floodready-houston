import { CalendarPlus } from 'lucide-react'
import { useApp } from '../../ctx'
import { Button, Card } from '../ds'
import { buildIcs, seasonEvents, type SeasonText } from './ics'

export default function SeasonReminders() {
  const { t, lang } = useApp()
  const tx: SeasonText = {
    start: t('p10.s.start'), startD: t('p10.s.startD'), ins: t('p10.s.ins'), insD: t('p10.s.insD'),
    bag: t('p10.s.bag'), bagD: t('p10.s.bagD'), stear: t('p10.s.stear'), stearD: t('p10.s.stearD'),
    monthly: t('p10.s.monthly'), monthlyD: t('p10.s.monthlyD'),
  }
  const fmt = new Intl.DateTimeFormat(lang, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  const evs = seasonEvents(tx)
  const download = () => {
    const url = URL.createObjectURL(new Blob([buildIcs(tx)], { type: 'text/calendar' }))
    const a = document.createElement('a')
    a.href = url; a.download = 'floodready-storm-season.ics'
    document.body.appendChild(a); a.click(); a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  return (
    <Card id="prepare-season" title={t('p10.s.h')} titleAs="h2" subtitle={t('p10.s.sub')}>
      <ul className="divide-y divide-line">
        {[...evs].sort((a, b) => a.date.getTime() - b.date.getTime()).map((e) => (
          <li key={e.id} className="py-2">
            <p className="text-body-sm font-semibold text-ink">{e.summary}</p>
            <p className="text-caption text-muted">{fmt.format(e.date)}{e.rrule ? ' · ' + t('p10.s.monthlyRep') : ''}</p>
          </li>
        ))}
      </ul>
      <Button className="mt-3" icon={CalendarPlus} onClick={download}>{t('p10.s.dl')}</Button>
      <p className="mt-2 text-caption text-muted">{t('p10.s.note')}</p>
    </Card>
  )
}
