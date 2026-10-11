import { forwardRef, type AnchorHTMLAttributes, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { LoaderCircle, type LucideIcon } from 'lucide-react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

const BASE = 'inline-flex select-none items-center justify-center gap-2 rounded-md font-semibold transition-colors duration-150 ease-out disabled:cursor-not-allowed disabled:opacity-50 aria-disabled:opacity-50'
const VARIANT: Record<ButtonVariant, string> = {
  primary: 'bg-brand text-brandink hover:bg-brand-strong active:bg-brand-strong',
  secondary: 'border border-ui bg-surface text-ink hover:bg-surface-2',
  ghost: 'text-brand hover:bg-brand-tint',
  danger: 'bg-danger text-white dark:text-bg hover:opacity-90',
}
const SIZE: Record<ButtonSize, string> = {
  sm: 'min-h-11 px-3 text-body-sm', // still a 44px target
  md: 'min-h-11 px-4 text-base',
  lg: 'min-h-13 px-5 text-base',
}
/** Class string for links styled as buttons. */
export const buttonClass = (variant: ButtonVariant = 'primary', size: ButtonSize = 'md', full = false) =>
  `${BASE} ${VARIANT[variant]} ${SIZE[size]} ${full ? 'w-full' : ''}`

interface Common { variant?: ButtonVariant; size?: ButtonSize; icon?: LucideIcon; iconEnd?: LucideIcon; loading?: boolean; full?: boolean; children?: ReactNode }

/** Button. md 44px / lg 52px. `loading` shows a spinner and keeps the width. */
export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & Common>(function Button(
  { variant = 'primary', size = 'md', icon: Icon, iconEnd: IconEnd, loading, full, className = '', children, disabled, type = 'button', ...p }, ref) {
  return (
    <button ref={ref} type={type} {...p} disabled={disabled || loading} aria-busy={loading || undefined}
      className={`${buttonClass(variant, size, full)} relative ${className}`}>
      {loading && <LoaderCircle aria-hidden size={16} className="absolute animate-spin" />}
      <span className={`inline-flex items-center gap-2 ${loading ? 'invisible' : ''}`}>
        {Icon && <Icon aria-hidden size={size === 'lg' ? 20 : 18} />}
        {children}
        {IconEnd && <IconEnd aria-hidden size={18} />}
      </span>
    </button>
  )
})

/** Anchor that looks like a Button. */
export function ButtonLink({ variant = 'primary', size = 'md', icon: Icon, iconEnd: IconEnd, full, className = '', children, ...p }:
  AnchorHTMLAttributes<HTMLAnchorElement> & Omit<Common, 'loading'>) {
  return (
    <a {...p} className={`${buttonClass(variant, size, full)} ${className}`}>
      {Icon && <Icon aria-hidden size={size === 'lg' ? 20 : 18} />}
      {children}
      {IconEnd && <IconEnd aria-hidden size={18} />}
    </a>
  )
}

/** Square 44x44 icon-only button. `label` is the accessible name (required). */
export const IconButton = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { icon: LucideIcon; label: string; variant?: 'ghost' | 'secondary' }>(
  function IconButton({ icon: Icon, label, variant = 'ghost', className = '', type = 'button', ...p }, ref) {
    const v = variant === 'secondary' ? 'border border-ui bg-surface text-ink hover:bg-surface-2' : 'text-ink hover:bg-surface-2'
    return (
      <button ref={ref} type={type} aria-label={label} title={label} {...p}
        className={`inline-flex size-11 shrink-0 items-center justify-center rounded-md transition-colors duration-150 disabled:opacity-50 ${v} ${className}`}>
        <Icon aria-hidden size={20} />
      </button>
    )
  })
