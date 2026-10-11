import { useEffect, useId, useRef } from 'react'
import { Captions, CaptionsOff, Keyboard, Mic, MicOff, PhoneOff, X } from 'lucide-react'
import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'
import { LiveOrb, type LiveOrbState } from './VoiceOrb'

export interface CaptionLine { id: number; role: 'user' | 'model'; text: string; final: boolean }

export interface VoiceModeProps {
  open: boolean
  state: LiveOrbState
  reconnecting: boolean
  thinkingLabel: string | null
  lines: CaptionLine[]
  captions: boolean
  onCaptions: (on: boolean) => void
  muted: boolean
  onMute: (on: boolean) => void
  ptt: boolean
  onPtt: (down: boolean) => void
  onEnd: () => void
  onType?: () => void
  latencyMs: number | null
  levels: () => { mic: number; out: number }
}

const isField = (el: EventTarget | null) => el instanceof HTMLElement && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable)

/**
 * Full-screen voice mode: bottom sheet on mobile, centered overlay on desktop (native <dialog>:
 * focus trap, Esc ends). Space bar or the big button = push-to-talk.
 */
export function VoiceMode(p: VoiceModeProps) {
  const { t } = useApp()
  const { demo } = useDemoMode()
  const ref = useRef<HTMLDialogElement>(null)
  const pttRef = useRef<HTMLButtonElement>(null)
  const capRef = useRef<HTMLDivElement>(null)
  const tid = useId()
  const pRef = useRef(p)
  useEffect(() => { pRef.current = p })

  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (p.open && !d.open) {
      const prev = document.activeElement as HTMLElement | null
      try { d.showModal() } catch { d.setAttribute('open', '') }
      d.focus()
      const html = document.documentElement
      const ov = html.style.overflow
      html.style.overflow = 'hidden'
      return () => { html.style.overflow = ov; if (d.open) d.close(); prev?.focus?.() }
    }
    if (!p.open && d.open) d.close()
  }, [p.open])

  // Space bar push-to-talk, anywhere in the dialog except on other buttons and fields.
  useEffect(() => {
    if (!p.open) return
    const skip = (e: KeyboardEvent) => isField(e.target) || (e.target instanceof HTMLButtonElement && e.target !== pttRef.current)
    const down = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || skip(e)) return
      e.preventDefault()
      if (!e.repeat) pRef.current.onPtt(true)
    }
    const up = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || skip(e)) return
      e.preventDefault(); pRef.current.onPtt(false)
    }
    const blur = () => pRef.current.onPtt(false)
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)
    window.addEventListener('blur', blur)
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); window.removeEventListener('blur', blur) }
  }, [p.open])

  useEffect(() => { const c = capRef.current; if (c) c.scrollTop = c.scrollHeight }, [p.lines])

  const label = p.reconnecting ? t('p8.state.reconnecting') : t('p8.state.' + p.state)
  const detail = p.state === 'thinking' ? (p.thinkingLabel || t('p8.thinking.default')) : ''
  const lastFinalModel = [...p.lines].reverse().find((l) => l.role === 'model' && l.final)
  const shown = p.lines.slice(-6)

  return (
    <dialog ref={ref} aria-labelledby={tid} tabIndex={-1} data-testid="voice-mode"
      onCancel={(e) => { e.preventDefault(); p.onEnd() }}
      className={'fixed m-0 hidden max-h-none max-w-none flex-col overflow-hidden border-0 bg-surface p-0 text-ink shadow-raised outline-none open:flex '
        + 'inset-x-0 top-auto bottom-0 h-[94dvh] w-full rounded-t-2xl '
        + 'md:inset-0 md:m-auto md:h-[min(760px,92vh)] md:w-[min(560px,92vw)] md:rounded-2xl '
        + 'backdrop:bg-[rgb(15_27_42/0.6)] motion-safe:open:animate-[fr-sheet-up_200ms_ease-out]'}>
      {p.open && <>
        <span aria-hidden className="mx-auto mt-2 block h-1 w-9 shrink-0 rounded-full bg-line md:hidden" />
        <header className="flex shrink-0 items-center justify-between gap-2 py-1 ps-4 pe-1">
          <h2 id={tid} className="text-h3 text-ink">{t('p8.title')}</h2>
          <div className="flex items-center">
            <button type="button" onClick={() => p.onCaptions(!p.captions)} aria-pressed={p.captions} aria-label={t('p8.captions')}
              className={'inline-flex size-11 items-center justify-center rounded-md hover:bg-surface-2 ' + (p.captions ? 'text-brand' : 'text-muted')}>
              {p.captions ? <Captions aria-hidden size={22} /> : <CaptionsOff aria-hidden size={22} />}
            </button>
            <button type="button" onClick={p.onEnd} aria-label={t('p8.endLabel')}
              className="inline-flex size-11 items-center justify-center rounded-md text-ink hover:bg-surface-2"><X aria-hidden size={22} /></button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-5 px-4">
          <LiveOrb state={p.reconnecting ? 'connecting' : p.state} levels={p.levels} />
          <div className="text-center">
            <p role="status" aria-live="polite" data-testid="voice-state" className="text-[19px] font-semibold leading-7 text-ink">
              {label}{detail && <span className="sr-only"> {detail}</span>}
            </p>
            <p aria-hidden className="mt-1 min-h-6 text-body text-muted">{detail}</p>
            {demo && p.latencyMs != null && (
              <p data-testid="voice-latency" className="mt-1 text-body-sm text-muted">{t('p8.latency').replace('{s}', (p.latencyMs / 1000).toFixed(1))}</p>
            )}
          </div>
        </div>

        {p.captions && (
          <div ref={capRef} aria-hidden className="max-h-[28%] min-h-24 shrink-0 space-y-2 overflow-y-auto overscroll-contain px-5 pb-2" data-testid="voice-captions">
            {shown.length === 0
              ? <p className="text-center text-body text-muted">{t('p8.captions.empty')}</p>
              : shown.map((l) => (
                <p key={l.id} className={'text-[17px] leading-7 ' + (l.role === 'user' ? 'text-end text-muted' : 'text-ink') + (l.final ? '' : ' opacity-70')}>
                  {l.text}
                </p>
              ))}
          </div>
        )}
        {/* Screen readers hear each finished answer once, captions on or off. */}
        <p className="sr-only" aria-live="polite">{lastFinalModel ? `${t('p4.live.assistant')}: ${lastFinalModel.text}` : ''}</p>

        <div className="shrink-0 border-t border-line px-4 pt-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">
          <div className="flex items-center justify-center gap-4">
            <button type="button" onClick={() => p.onMute(!p.muted)} aria-pressed={p.muted} aria-label={p.muted ? t('p8.unmute') : t('p8.mute')}
              className={'inline-flex size-14 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-150 '
                + (p.muted ? 'border-ink bg-ink text-surface' : 'border-line bg-surface-2 text-ink hover:border-ui')}>
              {p.muted ? <MicOff aria-hidden size={24} /> : <Mic aria-hidden size={24} />}
            </button>
            <button ref={pttRef} type="button" aria-pressed={p.ptt} data-testid="voice-ptt"
              aria-describedby={tid + '-ptt'}
              onPointerDown={(e) => { e.preventDefault(); e.currentTarget.setPointerCapture?.(e.pointerId); p.onPtt(true) }}
              onPointerUp={() => p.onPtt(false)} onPointerCancel={() => p.onPtt(false)} onLostPointerCapture={() => p.onPtt(false)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.repeat) { e.preventDefault(); p.onPtt(true) } }}
              onKeyUp={(e) => { if (e.key === 'Enter') { e.preventDefault(); p.onPtt(false) } }}
              onContextMenu={(e) => e.preventDefault()}
              className={'flex h-14 min-w-0 max-w-[220px] flex-1 touch-none select-none flex-col items-center justify-center rounded-full px-4 font-semibold transition-colors duration-150 '
                + (p.ptt ? 'bg-brand-strong text-brandink' : 'bg-brand text-brandink')}>
              <span className="text-[16px] leading-5">{t('p8.ptt')}</span>
              <span id={tid + '-ptt'} className="hidden text-[12px] font-normal leading-4 opacity-90 md:block">{t('p8.ptt.hint')}</span>
            </button>
            <button type="button" onClick={p.onEnd} aria-label={t('p8.endLabel')} data-testid="voice-end"
              className="inline-flex size-14 shrink-0 items-center justify-center rounded-full bg-danger text-surface">
              <PhoneOff aria-hidden size={24} />
            </button>
          </div>
          {p.onType && (
            <div className="mt-3 flex justify-center">
              <button type="button" onClick={p.onType} className="inline-flex min-h-11 items-center gap-2 rounded-md px-3 text-body font-medium text-brand hover:bg-surface-2">
                <Keyboard aria-hidden size={18} />{t('p8.type')}
              </button>
            </div>
          )}
        </div>
      </>}
    </dialog>
  )
}
