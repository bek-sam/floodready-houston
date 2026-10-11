import { useEffect, useRef } from 'react'
import { Mic, MicOff } from 'lucide-react'
import { useApp } from '../../ctx'

export type OrbState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'paused' | 'error'

const BARS = [0.5, 0.85, 1, 0.7, 0.45]

/**
 * Large voice orb: the whole circle is the button. State shows by color, motion and a text label
 * (aria-live). Motion uses motion-safe: classes, so reduced-motion users get static shapes plus an
 * opacity pulse on a label dot only. Never red for listening.
 */
export function VoiceOrb({ state, onPress, disabled }: { state: OrbState; onPress: () => void; disabled?: boolean }) {
  const { t } = useApp()
  const label = t('p4.orb.' + state)
  const hint = t(`p4.orb.${state}.hint`)
  const fill = state === 'speaking' ? 'bg-water text-white' : state === 'thinking' ? 'bg-brand-strong text-brandink'
    : state === 'paused' || state === 'error' ? 'border-2 border-ui bg-surface-2 text-brand' : 'bg-brand text-brandink'
  return (
    <div className="flex flex-col items-center text-center">
      <div className="relative flex size-36 items-center justify-center min-[360px]:size-[168px]">
        {state === 'listening' && [0, 1, 2].map((i) => (
          <span key={i} aria-hidden className="absolute inset-0 rounded-full border-2 border-brand opacity-0 motion-safe:animate-ping"
            style={{ animationDelay: `${i * 0.5}s`, animationDuration: '1.6s' }} />
        ))}
        <button type="button" onClick={onPress} disabled={disabled} data-testid="voice-orb" data-state={state}
          aria-pressed={state === 'listening' || state === 'speaking' || state === 'thinking'}
          aria-label={hint ? `${label}. ${hint}` : label}
          className={`relative flex size-full items-center justify-center overflow-hidden rounded-full shadow-raised transition-colors duration-150 disabled:opacity-60 ${fill}`}>
          {state === 'thinking' && <span aria-hidden className="absolute inset-2 rounded-full border-4 border-transparent border-t-brandink motion-safe:animate-spin" style={{ animationDuration: '1.2s' }} />}
          {state === 'speaking'
            ? <span aria-hidden className="flex h-16 items-center gap-1.5">
                {BARS.map((h, i) => <span key={i} className="w-2 rounded-full bg-white motion-safe:animate-pulse" style={{ height: `${h * 100}%`, animationDelay: `${i * 0.12}s` }} />)}
              </span>
            : state === 'thinking' ? null
            : state === 'error' ? <MicOff aria-hidden size={48} className="text-muted" />
            : <Mic aria-hidden size={48} />}
        </button>
      </div>
      <p role="status" aria-live="polite" className="mt-4 flex items-center gap-2 text-[17px] font-semibold leading-6 text-ink">
        {state === 'listening' && <span aria-hidden className="size-2.5 rounded-full bg-brand motion-safe:animate-pulse motion-reduce:animate-[pulse_2s_ease-in-out_infinite]" />}
        {label}
      </p>
      {hint && <p className="mt-1 max-w-[34ch] text-body text-muted">{hint}</p>}
    </div>
  )
}

export type LiveOrbState = 'connecting' | 'listening' | 'user' | 'thinking' | 'speaking' | 'muted'

/**
 * Full-screen voice orb. Reacts every frame to the mic level (user) and the assistant output level
 * (speaking) by writing CSS transforms straight to the DOM (no React re-render per frame).
 * Reduced motion: no scaling or rotation; the level shows as ring opacity only.
 */
export function LiveOrb({ state, levels }: { state: LiveOrbState; levels: () => { mic: number; out: number } }) {
  const glow = useRef<HTMLSpanElement>(null)
  const core = useRef<HTMLSpanElement>(null)
  const ring = useRef<HTMLSpanElement>(null)
  const stateRef = useRef(state)
  const levelsRef = useRef(levels)
  useEffect(() => { stateRef.current = state; levelsRef.current = levels })
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    let raf = 0, sm = 0
    const tick = () => {
      const st = stateRef.current
      const { mic, out } = levelsRef.current()
      const target = st === 'speaking' ? out : st === 'user' || st === 'listening' ? mic : 0
      sm += (target - sm) * (target > sm ? 0.5 : 0.12) // fast attack, slow release
      const reduce = !!mq?.matches
      const breathe = st === 'listening' && !reduce ? Math.sin(performance.now() / 700) * 0.015 : 0
      if (core.current) core.current.style.transform = reduce ? '' : `scale(${1 + breathe + sm * 0.14})`
      if (glow.current) {
        glow.current.style.transform = reduce ? '' : `scale(${1.02 + sm * 0.45})`
        glow.current.style.opacity = String(0.25 + sm * 0.75)
      }
      if (ring.current) ring.current.style.opacity = String(reduce ? 0.2 + sm * 0.8 : 0)
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])
  const tone = state === 'speaking' ? 'var(--water)' : state === 'thinking' ? 'var(--brand-strong)' : state === 'muted' || state === 'connecting' ? 'var(--ui)' : 'var(--brand)'
  return (
    <div aria-hidden data-testid="live-orb" data-state={state}
      className="relative flex size-[min(62vw,240px)] items-center justify-center md:size-[260px]">
      <span ref={glow} className="absolute inset-0 rounded-full blur-2xl transition-[background] duration-300"
        style={{ background: `radial-gradient(circle, ${tone} 0%, transparent 70%)` }} />
      <span ref={ring} className="absolute -inset-3 rounded-full border-4 opacity-0" style={{ borderColor: tone }} />
      {state === 'thinking' && (
        <span className="absolute -inset-1 rounded-full motion-safe:animate-spin"
          style={{ animationDuration: '1.4s', background: `conic-gradient(from 0deg, transparent 0 60%, ${tone} 100%)`,
            mask: 'radial-gradient(circle, transparent 66%, #000 67%)', WebkitMask: 'radial-gradient(circle, transparent 66%, #000 67%)' }} />
      )}
      <span ref={core} className="relative size-[78%] rounded-full shadow-raised transition-[background] duration-300 will-change-transform"
        style={{ background: `radial-gradient(circle at 35% 30%, color-mix(in srgb, ${tone} 55%, white) 0%, ${tone} 55%, color-mix(in srgb, ${tone} 70%, black) 100%)` }}>
        {state === 'connecting' && <span className="absolute inset-0 rounded-full bg-surface/30 motion-safe:animate-pulse" />}
        {state === 'muted' && <MicOff size={56} className="absolute inset-0 m-auto text-white" />}
      </span>
    </div>
  )
}
