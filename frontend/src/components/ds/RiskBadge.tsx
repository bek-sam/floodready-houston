import { LEVEL_CLASS, LEVEL_ICON, type Level } from '../../lib/levels'

const SIZE = {
  sm: { box: 'h-6 px-2 gap-1 text-caption font-semibold', icon: 14 },
  md: { box: 'h-8 px-3 gap-1.5 text-body-sm font-semibold', icon: 16 },
  lg: { box: 'min-h-11 px-4 gap-2 text-[20px] leading-7 font-bold', icon: 22 },
} as const

/** Pill with icon + text label (never color alone). Bg = tint, text/icon = level color. */
export function RiskBadge({ level, label, size = 'md', suffix, className = '' }: {
  level: Level; label: string; size?: 'sm' | 'md' | 'lg'; suffix?: string; className?: string
}) {
  const c = LEVEL_CLASS[level] ?? LEVEL_CLASS.unknown
  const Icon = LEVEL_ICON[level] ?? LEVEL_ICON.unknown
  const s = SIZE[size]
  return (
    <span className={`inline-flex max-w-full items-center whitespace-nowrap rounded-full border tabular-nums ${c.bg} ${c.text} ${c.border} ${s.box} ${className}`}>
      <Icon aria-hidden size={s.icon} className="shrink-0" />
      <span className="truncate">{label}{suffix}</span>
    </span>
  )
}
