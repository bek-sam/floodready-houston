import { forwardRef, useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from 'react'

export const inputCls = 'min-h-12 w-full rounded-sm border border-ui bg-surface px-3 py-2 text-base text-ink placeholder:text-muted/80 focus-visible:border-brand disabled:opacity-60'

/** Label + control + optional hint/error. Wrap one control. */
export function Field({ label, hint, error, children, className = '' }: { label: ReactNode; hint?: ReactNode; error?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-body-sm font-medium text-ink">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-caption text-muted">{hint}</span>}
      {error && <span role="alert" className="mt-1 block text-caption text-danger">{error}</span>}
    </label>
  )
}
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className = '', ...p }, ref) {
  return <input ref={ref} {...p} className={`${inputCls} ${className}`} />
})
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select({ className = '', ...p }, ref) {
  return <select ref={ref} {...p} className={`${inputCls} ${className}`} />
})
/** 24px checkbox with a 44px label hit area. */
export function Checkbox({ label, checked, onChange, description, className = '' }: {
  label: ReactNode; checked: boolean; onChange: (v: boolean) => void; description?: ReactNode; className?: string
}) {
  return (
    <label className={`flex min-h-11 cursor-pointer items-center gap-3 py-1 ${className}`}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="size-6 shrink-0 accent-[var(--brand)]" />
      <span className="min-w-0">
        <span className="block text-base text-ink">{label}</span>
        {description && <span className="block text-caption text-muted">{description}</span>}
      </span>
    </label>
  )
}
/** On/off switch (role=switch) with a label. */
export function Switch({ label, checked, onChange, description, disabled }: {
  label: ReactNode; checked: boolean; onChange: (v: boolean) => void; description?: ReactNode; disabled?: boolean
}) {
  const id = useId()
  return (
    <div className="flex min-h-13 items-center gap-3">
      <span className="min-w-0 flex-1">
        <span id={id} className="block text-base font-medium text-ink">{label}</span>
        {description && <span className="block text-caption text-muted">{description}</span>}
      </span>
      <button type="button" role="switch" aria-checked={checked} aria-labelledby={id} disabled={disabled} onClick={() => onChange(!checked)}
        className="inline-flex min-h-11 min-w-13 shrink-0 items-center justify-center disabled:opacity-50">
        <span aria-hidden className={`relative inline-block h-7 w-12 rounded-full border transition-colors duration-150 ${checked ? 'border-brand bg-brand' : 'border-ui bg-surface-2'}`}>
          <span className={`absolute top-0.5 size-5.5 rounded-full shadow-card transition-all duration-150 ${checked ? 'start-[22px] bg-brandink' : 'start-0.5 bg-ui'}`} />
        </span>
      </button>
    </div>
  )
}
