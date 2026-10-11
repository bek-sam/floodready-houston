import { useState } from 'react'
import { Phone } from 'lucide-react'
import { api } from '../api'
import { HOUSTON, useApp } from '../ctx'
import { placeName, usePlace } from '../state/place'
import { Button, ButtonLink, Card, ErrorBox, SkeletonText, SourceLink } from './ds'
import { useAsync } from './ui'

export const needsMedical = (s: string) => /dialy|oxygen|ox[ií]geno|ventilat|concentrator|di[aá]lisis/i.test(s)

/** Dialysis centers near My place. Runs when the household has dialysis, or when the user asks. */
export default function MedicalAccess() {
  const { t } = useApp()
  const { place, household } = usePlace()
  const [asked, setAsked] = useState(false)
  const on = household.medical.dialysis || asked
  const loc = place ?? HOUSTON
  const m = useAsync(() => api.medical({ lat: loc.lat, lon: loc.lon }, 5), [loc.lat, loc.lon], on)
  const name = placeName(place?.nickname, t)
  return (
    <Card title={t('p5a.med.h')} subtitle={t('p5a.med.hint')}>
      <p className="text-body-sm font-semibold text-ink" role="note">{t('c5.med.early')}</p>
      {!place && <p className="mt-2 text-body-sm text-muted">{t('p5a.med.noPlace')}</p>}
      {!on && <Button className="mt-3" variant="secondary" icon={Phone} onClick={() => setAsked(true)}>{t('p5a.med.find').replace('{name}', name)}</Button>}
      {on && m.loading && <div className="mt-3" aria-busy="true"><SkeletonText lines={3} /></div>}
      {on && m.error && <div className="mt-3"><ErrorBox error={t('c5.med.unavail')} onRetry={m.reload} /></div>}
      {on && m.data && (m.data.facilities ?? []).length === 0 && <p className="mt-3 text-body-sm text-muted">{t('c5.med.none')}</p>}
      <ul className="mt-2 divide-y divide-line">
        {(on ? m.data?.facilities ?? [] : []).map((f, i) => (
          <li key={i} className="flex items-center justify-between gap-3 py-3">
            <div className="min-w-0 text-body-sm">
              <p className="font-semibold text-ink">{f.name} <span className="font-normal text-muted">{typeof f.distance_mi === 'number' ? `· ${f.distance_mi.toFixed(1)} mi` : ''}</span></p>
              <p className="text-muted">{f.address}</p>
              {(f.sfha || f.harvey_flooded) && (
                <p className="mt-1 flex flex-wrap gap-1">
                  {f.sfha && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-caption font-semibold text-ink">{t('p39c.med.zone').replace('{z}', f.fema_zone ?? '')}</span>}
                  {f.harvey_flooded && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-caption font-semibold text-ink">{t('p39c.med.harvey')}</span>}
                </p>
              )}
            </div>
            {typeof f.phone === 'string' && f.phone && (
              <ButtonLink variant="secondary" icon={Phone} href={`tel:${f.phone.replace(/[^\d+]/g, '')}`} aria-label={t('p5a.med.callName').replace('{name}', f.name)}>{t('p5a.med.call')}</ButtonLink>
            )}
          </li>
        ))}
      </ul>
      {on && m.data && <p className="mt-2 text-caption text-muted">{t('p39.med.note')} {(m.data.facilities ?? []).some((f) => f.sfha != null || f.harvey_flooded != null) && t('p39c.med.call') + ' '}<SourceLink href={m.data.source} /></p>}
    </Card>
  )
}
