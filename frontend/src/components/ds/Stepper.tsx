import { useApp } from '../../ctx'

/** "Step 2 of 3" + segment bars. `current` is 0-based. */
export function Stepper({ steps, current, className = '' }: { steps: string[]; current: number; className?: string }) {
  const { t } = useApp()
  const label = t('ds.stepOf').replace('{n}', String(current + 1)).replace('{m}', String(steps.length))
  return (
    <div className={className}>
      <p className="text-caption text-muted" aria-live="polite">
        {label}{steps[current] ? <span className="sr-only">: {steps[current]}</span> : null}
      </p>
      <div className="mt-2 flex gap-1" aria-hidden>
        {steps.map((s, i) => <span key={s + i} className={`h-1 flex-1 rounded-full ${i <= current ? 'bg-brand' : 'bg-line'}`} />)}
      </div>
    </div>
  )
}
