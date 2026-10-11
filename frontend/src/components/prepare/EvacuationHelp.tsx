import { ExternalLink, Phone } from 'lucide-react'
import { useApp } from '../../ctx'
import { ButtonLink, Card, SourceLink } from '../ds'

/** If you need help to evacuate. Content shortened from data/knowledge/special-needs-and-no-car.md. */
export default function EvacuationHelp() {
  const { t } = useApp()
  return (
    <Card title={t('p5a.evac.h')} titleAs="h2">
      <ul className="divide-y divide-line">
        <li className="py-3">
          <p className="font-semibold text-ink">{t('p5a.evac.stear')}</p>
          <p className="mt-0.5 text-body-sm text-muted">{t('p5a.evac.stearD')}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ButtonLink variant="primary" iconEnd={ExternalLink} href="https://stear.texas.gov" target="_blank" rel="noreferrer">{t('p5a.evac.online')}</ButtonLink>
            <ButtonLink variant="secondary" icon={Phone} href="tel:211">{t('p5a.evac.call211')}</ButtonLink>
          </div>
          <p className="mt-2"><SourceLink href="https://tdem.texas.gov/stear" /></p>
        </li>
        <li className="py-3">
          <p className="font-semibold text-ink">{t('p5a.evac.c211')}</p>
          <p className="mt-0.5 text-body-sm text-muted">{t('p5a.evac.c211D')}</p>
          <p className="mt-1"><SourceLink href="https://www.211texas.org/" /></p>
        </li>
        <li className="py-3">
          <p className="font-semibold text-ink">{t('p5a.evac.c311')}</p>
          <p className="mt-0.5 text-body-sm text-muted">{t('p5a.evac.c311D')}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ButtonLink variant="secondary" icon={Phone} href="tel:311">{t('p5a.evac.call311')}</ButtonLink>
            <ButtonLink variant="danger" icon={Phone} href="tel:911">{t('p5a.evac.call911')}</ButtonLink>
          </div>
          <p className="mt-2"><SourceLink href="https://www.readyharris.org/" /></p>
        </li>
      </ul>
    </Card>
  )
}
