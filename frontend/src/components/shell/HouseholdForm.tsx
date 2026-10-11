import { useApp } from '../../ctx'
import type { Household } from '../../state/place'
import { Checkbox, Segmented } from '../ds'

/** Controlled household editor (onboarding step 3 and the household sheet). */
export function HouseholdForm({ value: h, onChange }: { value: Household; onChange: (h: Household) => void }) {
  const { t } = useApp()
  const med = (k: keyof Household['medical'], v: boolean) => onChange({ ...h, medical: { ...h.medical, [k]: v } })
  return (
    <div className="space-y-5">
      <Segmented label={t('hh.tenure')} value={h.renter === null ? null : h.renter ? 'rent' : 'own'}
        onChange={(v) => onChange({ ...h, renter: v === 'rent' })}
        options={[{ value: 'rent', label: t('hh.rent') }, { value: 'own', label: t('hh.own') }]} />
      <div>
        <p className="mb-1 text-body-sm font-medium text-ink">{t('hh.carQ')}</p>
        <Segmented label={t('hh.carQ')} value={h.hasCar === null ? null : h.hasCar ? 'yes' : 'no'}
          onChange={(v) => onChange({ ...h, hasCar: v === 'yes' })}
          options={[{ value: 'yes', label: t('hh.yes') }, { value: 'no', label: t('hh.no') }]} />
      </div>
      <fieldset>
        <legend className="mb-1 text-body-sm font-medium text-ink">{t('hh.needs')}</legend>
        <Checkbox label={t('hh.dialysis')} checked={h.medical.dialysis} onChange={(v) => med('dialysis', v)} />
        <Checkbox label={t('hh.oxygen')} checked={h.medical.oxygen} onChange={(v) => med('oxygen', v)} />
        <Checkbox label={t('hh.powerDevice')} checked={h.medical.powerDevice} onChange={(v) => med('powerDevice', v)} />
        <Checkbox label={t('hh.walking')} checked={h.mobility !== 'none'} onChange={(v) => onChange({ ...h, mobility: v ? 'some' : 'none' })} />
      </fieldset>
      <fieldset>
        <legend className="mb-1 text-body-sm font-medium text-ink">{t('hh.whoElse')}</legend>
        <Checkbox label={t('hh.kidsL')} checked={h.ages.kids} onChange={(v) => onChange({ ...h, ages: { ...h.ages, kids: v } })} />
        <Checkbox label={t('hh.olderL')} checked={h.ages.older} onChange={(v) => onChange({ ...h, ages: { ...h.ages, older: v } })} />
        <Checkbox label={t('hh.petsL')} checked={h.pets} onChange={(v) => onChange({ ...h, pets: v })} />
      </fieldset>
    </div>
  )
}
