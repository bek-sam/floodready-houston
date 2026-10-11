import { useCallback, useEffect, useRef, useState } from 'react'
import { LiveSession, b64json, type LiveEvent, type Role } from '../audio/live'
import { useApp } from '../ctx'
import { toProfile, usePlace } from '../state/place'
import { toast } from './ds'
import { VoiceOrb, type LiveOrbState } from './ask/VoiceOrb'
import { VoiceMode, type CaptionLine } from './ask/VoiceMode'

function errKey(e: unknown): string | null {
  const n = (e as { name?: string })?.name
  if (n === 'NotAllowedError' || n === 'SecurityError') return 'p4.live.denied'
  if (n === 'NotFoundError') return 'p4.live.nomic'
  return null
}

const CAPTIONS_KEY = 'floodready.voiceCaptions'
const CONNECT_WATCHDOG_MS = 12000
const USER_LEVEL = 0.1 // orb "user speaking" threshold on the 0..1 mic level
const USER_HANGOVER_MS = 350

type Phase = 'idle' | 'connecting' | 'live' | 'reconnecting'

/**
 * Voice (Gemini Live) controller: owns the LiveSession and renders the inline launcher plus the
 * full-screen VoiceMode overlay. Falls back to the compatibility engine via onFallback.
 */
export default function LiveTalk({ lang, lat, lon, onFallback, onType }: {
  lang: string; lat?: number; lon?: number; onFallback?: () => void; onType?: () => void
}) {
  const { t } = useApp()
  const { place, household } = usePlace()
  const [phase, setPhase] = useState<Phase>('idle')
  const [err, setErr] = useState('')
  const [lines, setLines] = useState<CaptionLine[]>([])
  const [playing, setPlaying] = useState(false)
  const [userTalking, setUserTalking] = useState(false)
  const [thinking, setThinking] = useState<string | null | false>(false) // false = not thinking, null = generic label
  const [muted, setMuted] = useState(false)
  const [ptt, setPttState] = useState(false)
  const [latency, setLatency] = useState<number | null>(null)
  const [captions, setCaptionsState] = useState(() => { try { return localStorage.getItem(CAPTIONS_KEY) !== '0' } catch { return true } })
  const sess = useRef<LiveSession | null>(null)
  const id = useRef(0)
  const hasCaptions = useRef(false)
  const pttRef = useRef(false)

  const setCaptions = (v: boolean) => { setCaptionsState(v); try { localStorage.setItem(CAPTIONS_KEY, v ? '1' : '0') } catch { /* ignore */ } }
  useEffect(() => () => { sess.current?.stop(); sess.current = null }, [])

  // Connect watchdog: never sit on "Connecting…" forever.
  useEffect(() => {
    if (phase !== 'connecting' && phase !== 'reconnecting') return
    const h = setTimeout(() => fail(), CONNECT_WATCHDOG_MS)
    return () => clearTimeout(h)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase])

  // "User speaking" from the mic analyser, polled at 10 Hz with a short hangover (the orb itself animates per frame).
  useEffect(() => {
    if (phase !== 'live') { setUserTalking(false); return }
    let last = 0
    const iv = setInterval(() => {
      const s = sess.current
      if (!s) return
      const now = performance.now()
      if (s.levels().mic > USER_LEVEL) last = now
      setUserTalking(now - last < USER_HANGOVER_MS)
    }, 100)
    return () => clearInterval(iv)
  }, [phase])

  /** Partial/final captions. Partials may be deltas or the running text; finals may repeat the whole line. */
  const caption = useCallback((role: Role, text: string, final: boolean) => {
    setLines((ls) => {
      let idx = -1
      for (let i = ls.length - 1; i >= 0; i--) if (ls[i].role === role) { if (!ls[i].final) idx = i; break }
      if (idx < 0) {
        if (!text.trim()) return ls
        return [...ls, { id: ++id.current, role, text: text.trimStart(), final }].slice(-40)
      }
      const cur = ls[idx].text
      const next = !text ? cur : text.startsWith(cur) || (final && text.length >= cur.length) ? text : cur + text
      const out = ls.slice()
      out[idx] = { ...ls[idx], text: next.trimStart(), final }
      return out
    })
  }, [])
  const finalize = useCallback((role?: Role) => setLines((ls) => ls.some((l) => !l.final && (!role || l.role === role))
    ? ls.map((l) => (!l.final && (!role || l.role === role) ? { ...l, final: true } : l)) : ls), [])

  const onEvent = useCallback((e: LiveEvent) => {
    switch (e.type) {
      case 'ready': setPhase('live'); break
      case 'reconnecting': setPhase('reconnecting'); setPlaying(false); setThinking(false); finalize(); break
      case 'reconnected': setPhase('live'); break
      case 'playing': setPlaying(e.on); if (e.on) setThinking(false); break
      case 'caption':
        hasCaptions.current = true
        if (e.role === 'model') setThinking(false)
        else finalize('model') // user started a new turn
        caption(e.role, e.text ?? '', !!e.final)
        break
      case 'transcript': // pre-v2 servers: deltas only
        if (hasCaptions.current) break
        if (e.role === 'model') { setThinking(false); finalize('user') } else finalize('model')
        caption(e.role, e.text ?? '', false)
        break
      case 'thinking': setThinking((x) => e.label || (typeof x === 'string' ? x : null)); break // label=null: tool done, keep the last label until the answer starts
      case 'tool': setThinking((x) => (x === false ? null : x)); break
      case 'turn':
        if (e.event === 'user_end') { finalize('user'); setThinking((x) => (x === false ? null : x)) }
        else if (e.event === 'model_start') setThinking(false)
        else if (e.event === 'model_end') finalize('model')
        break
      case 'interrupted': setPlaying(false); setThinking(false); finalize('model'); break
      case 'latency': setLatency(Math.round(e.ms)); break
      case 'error': setErr(e.detail || t('p4.live.fail')); break
    }
  }, [caption, finalize, t])

  function cleanup() {
    sess.current?.stop(); sess.current = null
    setPhase('idle'); setPlaying(false); setThinking(false); setPttState(false); pttRef.current = false
    finalize()
  }

  /** Live failed (initial connect or after the one reconnect): switch to the compatibility engine. */
  function fail() {
    cleanup()
    if (onFallback) { toast({ message: t('p8.fallback') }); onFallback() }
    else setErr(t('p4.live.fail'))
  }

  async function begin() {
    if (sess.current) return
    setErr(''); setLines([]); setLatency(null); setMuted(false); hasCaptions.current = false
    setPhase('connecting')
    const s = new LiveSession({
      onEvent,
      onClose: ({ failed }) => { if (sess.current !== s) return; if (failed) fail(); else cleanup() },
    })
    sess.current = s
    try {
      await s.start({
        lang, lat: place?.lat ?? lat, lon: place?.lon ?? lon, place: place?.label || undefined,
        profile: b64json(toProfile(household, place, lang)),
      })
      if (sess.current === s) setPhase((p) => (p === 'connecting' ? 'live' : p))
    } catch (e) {
      if (sess.current !== s) return
      const k = errKey(e)
      if (k) { cleanup(); setErr(t(k)) } else fail()
    }
  }

  const end = () => cleanup()
  const toType = () => { cleanup(); onType?.() }
  const mute = (on: boolean) => { setMuted(on); sess.current?.setMuted(on) }
  const setPtt = useCallback((down: boolean) => {
    if (pttRef.current === down) return
    pttRef.current = down; setPttState(down)
    sess.current?.setPtt(down)
    if (down) { setPlaying(false); finalize('model') }
  }, [finalize])
  const levels = useCallback(() => sess.current?.levels() ?? { mic: 0, out: 0 }, [])

  const orb: LiveOrbState = phase === 'connecting' || phase === 'reconnecting' ? 'connecting'
    : muted && !ptt ? 'muted'
    : ptt || (userTalking && !playing) ? 'user'
    : playing ? 'speaking'
    : thinking !== false ? 'thinking'
    : 'listening'
  const open = phase !== 'idle'
  const past = lines.filter((l) => l.final && l.text.trim())

  return (
    <section aria-label={t('p8.dialog')} className="space-y-4">
      <VoiceOrb state="idle" onPress={begin} disabled={open} />
      {err && <p role="alert" className="text-center text-body-sm text-danger">{err}</p>}
      {!open && past.length > 0 && (
        <div role="log" aria-label={t('p4.live.log')} className="max-h-72 space-y-2 overflow-y-auto">
          <p className="text-overline uppercase text-muted">{t('p8.recent')}</p>
          {past.map((m) => (
            <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex'}>
              <p className={'max-w-[85%] rounded-lg px-3 py-2 text-body ' + (m.role === 'user' ? 'bg-brand text-brandink' : 'border border-line bg-surface text-ink')}>
                <span className="sr-only">{m.role === 'user' ? t('p4.live.you') : t('p4.live.assistant')}: </span>{m.text}
              </p>
            </div>
          ))}
        </div>
      )}
      <VoiceMode open={open} state={orb} reconnecting={phase === 'reconnecting'} thinkingLabel={typeof thinking === 'string' ? thinking : null}
        lines={lines} captions={captions} onCaptions={setCaptions} muted={muted} onMute={mute} ptt={ptt} onPtt={setPtt}
        onEnd={end} onType={onType ? toType : undefined} latencyMs={latency} levels={levels} />
    </section>
  )
}
