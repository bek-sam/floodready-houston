import { AlertTriangle, ExternalLink, Phone } from 'lucide-react'
import type { Civic } from '../../api'
import { useApp } from '../../ctx'
import { ButtonLink, Card } from '../ds'

// Verified from official pages: Houston 311 = 311 or 713-837-0311, portal https://houston311.powerappsportals.us/en-US/
// (specific street-flooding request type not verifiable from the page, so we describe it in text and link the portal).
// HCFCD = 346-286-4000, https://www.hcfcd.org/Community/Contact-Us/Service-Request (bayou/channel concerns).
export const HOUSTON_311_URL = 'https://houston311.powerappsportals.us/en-US/'
export const HCFCD_URL = 'https://www.hcfcd.org/Community/Contact-Us/Service-Request'

/** City of Houston when a city council member is on record; otherwise treated as unincorporated Harris County. */
export const isCityOfHouston = (civic?: Civic | null) => !!civic?.officials?.council

export default function Report311({ civic }: { civic?: Civic | null }) {
  const { t } = useApp()
  const city = civic ? isCityOfHouston(civic) : null
  return (
    <Card title={t('p11a.311.title')} subtitle={t('p11a.311.sub')}>
      <p className="flex items-start gap-2 rounded-md bg-surface-2 p-3 text-body-sm font-semibold text-ink"><AlertTriangle aria-hidden size={16} className="mt-0.5 shrink-0 text-danger" />{t('p11a.311.emerg')}</p>
      {city !== false && (
        <div className="mt-3">
          <p className="text-body-sm font-semibold text-ink">{t('p11a.311.city')}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ButtonLink variant="secondary" size="sm" icon={ExternalLink} href={HOUSTON_311_URL} target="_blank" rel="noreferrer">{t('p11a.311.street')}</ButtonLink>
            <ButtonLink variant="secondary" size="sm" icon={ExternalLink} href={HOUSTON_311_URL} target="_blank" rel="noreferrer">{t('p11a.311.drain')}</ButtonLink>
            <ButtonLink variant="secondary" size="sm" icon={Phone} href="tel:311">{t('p11a.311.call')} 311</ButtonLink>
            <ButtonLink variant="secondary" size="sm" icon={Phone} href="tel:7138370311">713-837-0311</ButtonLink>
          </div>
        </div>
      )}
      {city !== true && (
        <div className="mt-3">
          <p className="text-body-sm font-semibold text-ink">{t('p11a.311.county')}</p>
          <p className="text-caption text-muted">{t('p11a.311.countyNote')}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <ButtonLink variant="secondary" size="sm" icon={ExternalLink} href={HCFCD_URL} target="_blank" rel="noreferrer">{t('p11a.311.hcfcd')}</ButtonLink>
            <ButtonLink variant="secondary" size="sm" icon={Phone} href="tel:3462864000">{t('p11a.311.call')} 346-286-4000</ButtonLink>
          </div>
        </div>
      )}
      <p className="mt-3 text-caption text-muted">{t('p11a.311.note')}</p>
    </Card>
  )
}
