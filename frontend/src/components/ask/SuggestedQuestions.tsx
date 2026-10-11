import { useApp } from '../../ctx'
import { usePlace } from '../../state/place'

const BASE = ['street', 'zone', 'renters', 'start', 'nocar', 'drain']

/** Four chips personalized to My place and household: medical first if dialysis, renter first if renter. */
export function SuggestedQuestions({ onPick, disabled }: { onPick: (q: string) => void; disabled?: boolean }) {
  const { t } = useApp()
  const { household: h, place } = usePlace()
  const first: string[] = []
  if (h.medical.dialysis) first.push('dialysis')
  if (h.renter === true) first.push('renters')
  if (h.hasCar === false) first.push('nocar')
  if (!place) first.push('zone')
  const ids = [...first, ...BASE].filter((x, i, a) => a.indexOf(x) === i).slice(0, 4)
  return (
    <ul aria-label={t('p4.chips')} className="flex flex-wrap justify-center gap-2">
      {ids.map((id) => (
        <li key={id}>
          <button type="button" disabled={disabled} onClick={() => onPick(t('p4.q.' + id))}
            className="min-h-11 rounded-full border border-line bg-surface-2 px-4 py-2 text-start text-body text-ink hover:border-brand disabled:opacity-50">
            {t('p4.q.' + id)}
          </button>
        </li>
      ))}
    </ul>
  )
}
