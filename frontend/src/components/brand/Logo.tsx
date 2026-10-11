/** Shield + two waves mark (§5.1). Decorative; the lockup carries the text. */
export function LogoMark({ size = 24, className = '' }: { size?: number; className?: string }) {
  return (
    <svg aria-hidden width={size} height={size} viewBox="0 0 24 24" fill="none" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={`shrink-0 ${className}`}>
      <path d="M12 2.5 4 5.5v6c0 5 3.4 8.6 8 10 4.6-1.4 8-5 8-10v-6l-8-3Z" stroke="var(--brand)" />
      <path d="M7.5 11.5c1.1-.9 2.2-.9 3.3 0s2.2.9 3.3 0 2.2-.9 2.4-.2" stroke="var(--water)" />
      <path d="M9 15c1-.8 2-.8 3 0s2 .8 3 0" stroke="var(--water)" />
    </svg>
  )
}

/** Brand lockup: mark + "FloodReady" (700) + "Houston" (500 muted). `compact` hides "Houston". */
export function Lockup({ size = 24, compact = false, className = '', textClassName = '' }: { size?: number; compact?: boolean; className?: string; textClassName?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <LogoMark size={size} />
      <span className={`text-[17px] leading-6 tracking-[-0.01em] ${textClassName}`}>
        <span className="font-bold text-ink">FloodReady</span>
        {!compact && <span className="font-medium text-muted"> Houston</span>}
      </span>
    </span>
  )
}
