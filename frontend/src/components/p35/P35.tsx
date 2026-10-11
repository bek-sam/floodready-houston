import { Phone } from 'lucide-react'
import { api, type AirportsStatus } from '../../api'
import { useApp } from '../../ctx'
import { SourceLink } from '../ds'
import { useAsync } from '../ui'

const BUYOUT_SRC = 'https://www.hcfcd.org/Buyouts'
const BUYOUT_FORM = 'https://survey123.arcgis.com/share/dced0658099e45c5a2059748577d4beb'
const SMART_SRC = 'https://www.floodsmart.gov/flood-insurance-cost'
const FAA_SRC = 'https://nasstatus.faa.gov/'

/** HCFCD buyout hotline + volunteer form (no timeline claimed). */
export function BuyoutContact() {
  const { t } = useApp()
  return (
    <div className="rounded-md bg-surface-2 p-4 text-body-sm text-ink" role="note">
      <p className="text-h3">{t('p35.buy.h')}</p>
      <p className="mt-1 text-muted">{t('p35.buy.desc')}</p>
      <div className="mt-2 flex flex-col gap-2">
        <a href="tel:+13462864020" className="inline-flex min-h-12 items-center gap-2 font-semibold text-brand underline underline-offset-2"><Phone aria-hidden size={18} />{t('p35.buy.call')}</a>
        <a href={BUYOUT_FORM} target="_blank" rel="noreferrer" className="inline-flex min-h-12 items-center font-semibold text-brand underline underline-offset-2">{t('p35.buy.form')}</a>
      </div>
      <p className="mt-1 text-caption text-muted">{t('p35.buy.note')}<SourceLink href={BUYOUT_SRC} label={t('p35.buy.src')} /></p>
    </div>
  )
}

/** Ways to pay less, only FloodSmart-stated levers. */
export function PayLess() {
  const { t } = useApp()
  return (
    <div className="rounded-lg border border-line bg-surface p-4 text-body-sm text-ink">
      <h2 className="text-h3">{t('p35.save.h')}</h2>
      <ul className="mt-2 list-disc space-y-1 ps-5">
        <li>{t('p35.save.ec')}</li><li>{t('p35.save.elev')}</li><li>{t('p35.save.mod')}</li>
      </ul>
      <p className="mt-2 text-caption text-muted">{t('p35.save.note')}<SourceLink href={SMART_SRC} label={t('p35.save.src')} /></p>
    </div>
  )
}

/** IAH/HOU closure chip. Hidden when status is unknown. */
export function AirportChip() {
  const { t } = useApp()
  const a = useAsync<AirportsStatus>(() => api.airportsStatus(), [])
  const list = (a.data?.airports ?? []).filter((x) => x.closed != null)
  if (!list.length) return null
  return (
    <div className="rounded-lg border border-line bg-surface px-4 py-3 text-body-sm text-ink" role="status">
      <p className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="font-semibold">{t('p35.air.h')}</span>
        {list.map((x) => (
          <span key={x.code} className={x.closed ? 'font-semibold text-warning' : ''}>
            {t(x.closed ? 'p35.air.closed' : 'p35.air.open').replace('{code}', x.code)}
            {x.closed && x.reason ? ` (${x.reason})` : ''}
            {x.closed && x.reopen ? ', ' + t('p35.air.reopen').replace('{when}', x.reopen) : ''}
          </span>
        ))}
      </p>
      <p className="text-caption text-muted">{t('p35.air.note')}<SourceLink href={a.data?.source || FAA_SRC} label={t('p35.air.src')} /></p>
    </div>
  )
}
