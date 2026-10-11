import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Keyboard, MessageCircleQuestion, Mic, Settings2 } from 'lucide-react'
import { api, ApiError, type Ask } from '../api'
import { LANGS } from '../i18n'
import { useApp } from '../ctx'
import { speak, stopSpeaking, unlockAudio, createSpeechQueue, preloadFiller, type SpeechQueue } from '../components/speak'
import { Button, DemoPanel, EmptyState, IconButton, LoadingText, PageHeader, Segmented } from '../components/ds'
import { useDemoMode } from '../state/place'
import { clearDemoGo, peekDemoGo } from '../lib/demoGo'
import { SuggestedQuestions } from '../components/ask/SuggestedQuestions'
import { VoiceOrb, type OrbState } from '../components/ask/VoiceOrb'
import { MessageList, type Msg } from '../components/ask/MessageList'
import { Composer } from '../components/ask/Composer'
import { VoiceSettingsSheet, type Engine } from '../components/ask/VoiceSettingsSheet'

const LiveTalk = lazy(() => import('../components/LiveTalk'))
const ElAgentTalk = lazy(() => import('../components/ElAgentTalk'))
const ENGINE_KEY = 'floodready.voiceEngine'
const MODE_KEY = 'floodready.askMode'
const ALOUD_KEY = 'floodready.askAloud'
function loadEngine(): Engine {
  try { const v = localStorage.getItem(ENGINE_KEY); if (v === 'live' || v === 'el' || v === 'fast') return v } catch { /* ignore */ }
  return 'live' // Voice v2: Live is the default; "fast" = Voice (compatibility)
}
type AskMode = 'type' | 'talk'
function loadMode(): AskMode { try { return localStorage.getItem(MODE_KEY) === 'talk' ? 'talk' : 'type' } catch { return 'type' } }

interface SRInst {
  lang: string; interimResults: boolean; continuous: boolean
  onresult: ((e: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null
  onend: (() => void) | null; onerror: ((e: { error?: string }) => void) | null
  start: () => void; stop: () => void; abort: () => void
}
type SR = { new (): SRInst }
type TalkState = 'off' | 'listening' | 'thinking' | 'speaking' | 'paused'

/** Plain text for speech when the backend sends no `speak`: strip URLs/markdown, ~300 chars. */
function speakFallback(a: string): string {
  const s = a.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/https?:\/\/\S+/g, '').replace(/[*_`#>•]|^\s*-\s+/gm, '').replace(/\s+/g, ' ').trim()
  if (s.length <= 300) return s
  const cut = s.slice(0, 300)
  const i = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('? '), cut.lastIndexOf('! '))
  return i > 100 ? cut.slice(0, i + 1) : cut
}
const SpeechRec: SR | undefined = (window as unknown as { SpeechRecognition?: SR; webkitSpeechRecognition?: SR }).SpeechRecognition
  ?? (window as unknown as { webkitSpeechRecognition?: SR }).webkitSpeechRecognition

export default function AskPage() {
  const { t, lang, place } = useApp()
  const { demo } = useDemoMode()
  const [mode, setModeState] = useState<AskMode>(loadMode)
  const [sheet, setSheet] = useState(false)
  const [aloud, setAloudState] = useState(() => { try { return localStorage.getItem(ALOUD_KEY) === '1' } catch { return false } })
  const setMode = (m: AskMode) => { if (m === 'type' && activeRef.current) endTalk(); setModeState(m); try { localStorage.setItem(MODE_KEY, m) } catch { /* ignore */ } }
  const setAloud = (v: boolean) => { setAloudState(v); try { localStorage.setItem(ALOUD_KEY, v ? '1' : '0') } catch { /* ignore */ } }
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const [listening, setListening] = useState(false)
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null)
  const end = useRef<HTMLDivElement>(null)
  const lastPlace = place
  const [talk, setTalkState] = useState<TalkState>('off')
  const [interim, setInterim] = useState('')
  const [talkNote, setTalkNote] = useState('')
  const talkRef = useRef<TalkState>('off')
  const activeRef = useRef(false)
  const recRef = useRef<SRInst | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const silentRef = useRef(0)
  const gen = useRef(0)
  const [engineSel, setEngineState] = useState<Engine>(loadEngine)
  const engine: Engine = engineSel === 'el' && !demo ? 'fast' : engineSel
  const [lat, setLat] = useState<{ first: number; speech?: number; server?: number } | null>(null)
  const queueRef = useRef<SpeechQueue | null>(null)
  const setEngine = (e: Engine) => {
    if (activeRef.current) endTalk()
    setEngineState(e)
    try { localStorage.setItem(ENGINE_KEY, e) } catch { /* ignore */ }
  }
  const msgsRef = useRef<Msg[]>([])
  const langRef = useRef(lang); langRef.current = lang
  const placeRef = useRef(lastPlace); placeRef.current = lastPlace
  msgsRef.current = msgs
  const setTalk = (s: TalkState) => { talkRef.current = s; setTalkState(s) }
  useEffect(() => { if (msgs.length) end.current?.scrollIntoView({ block: 'nearest' }) }, [msgs])
  // Judge step 4: pre-fill the Spanish demo question in Type mode.
  useEffect(() => { if (peekDemoGo(4)) { clearDemoGo(); setModeState('type'); setQ('¿Qué hago si mi calle se inunda?') } }, [])
  useEffect(() => { if (engine === 'fast') void preloadFiller(lang) }, [engine, lang])
  useEffect(() => () => { queueRef.current?.cancel(); activeRef.current = false; gen.current++; recRef.current?.abort(); abortRef.current?.abort(); stopSpeaking() }, [])

  const killRec = () => {
    const r = recRef.current; recRef.current = null
    if (r) { r.onresult = null; r.onend = null; r.onerror = null; try { r.abort() } catch { /* ignore */ } }
  }
  const pauseTalk = () => { queueRef.current?.cancel(); gen.current++; killRec(); abortRef.current?.abort(); stopSpeaking(); setInterim(''); setTalk('paused') }
  const endTalk = (note = '') => {
    queueRef.current?.cancel(); activeRef.current = false; gen.current++; killRec(); abortRef.current?.abort(); stopSpeaking()
    setInterim(''); setTalkNote(note); setTalk('off')
  }

  const listen = () => {
    if (!activeRef.current || !SpeechRec) return
    if (document.hidden) { pauseTalk(); return }
    queueRef.current?.cancel(); abortRef.current?.abort(); killRec(); stopSpeaking()
    const my = ++gen.current
    const r = new SpeechRec()
    r.lang = LANGS.find((l) => l.code === langRef.current)?.speech ?? 'en-US'
    r.interimResults = true; r.continuous = false
    let got = false, finalText = '', lastTxt = ''
    r.onresult = (e) => {
      if (my !== gen.current) return
      let txt = ''
      for (let i = 0; i < e.results.length; i++) { txt += e.results[i][0].transcript; if (e.results[i].isFinal) finalText = txt }
      got = true; lastTxt = txt; setInterim(txt)
      if (finalText.trim()) { const f = finalText.trim(); recRef.current = null; r.onresult = null; r.onend = null; r.onerror = null; try { r.abort() } catch { /* ignore */ } turn(f) }
    }
    r.onerror = (e) => {
      if (my !== gen.current) return
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') endTalk(t('talk.denied'))
      else if (e.error === 'audio-capture') endTalk(t('talk.denied'))
    }
    r.onend = () => {
      if (my !== gen.current || !activeRef.current || talkRef.current !== 'listening') return
      recRef.current = null
      if (!finalText.trim() && lastTxt.trim()) { turn(lastTxt.trim()); return }
      if (!got) {
        silentRef.current += 1
        if (silentRef.current >= 2) { endTalk(t('talk.idle')); return }
      }
      setInterim(''); listen()
    }
    recRef.current = r; setInterim(''); setTalk('listening')
    try { r.start() } catch { endTalk(t('talk.unsupported')) }
  }

  const turn = async (text: string) => {
    silentRef.current = 0; setInterim(''); setTalk('thinking')
    const history = msgsRef.current.filter((m) => !m.error).slice(-6).map((m) => ({ role: m.role === 'user' ? 'user' as const : 'assistant' as const, content: m.text.slice(0, 600) }))
    setMsgs((m) => [...m, { role: 'user', text }])
    const ac = new AbortController(); abortRef.current = ac
    const my = ++gen.current
    const t0 = performance.now()
    const live = () => my === gen.current && activeRef.current
    let heard = false, spoke = false, firstMs = 0
    let finished: Ask | null = null
    let fillerTimer: ReturnType<typeof setTimeout> | null = null
    const clearFiller = () => { if (fillerTimer) { clearTimeout(fillerTimer); fillerTimer = null } }
    setLat(null)
    const q = createSpeechQueue(langRef.current, {
      onFirstAudio: (kind) => { firstMs = Math.round(performance.now() - t0); if (live()) { setTalk('speaking'); setLat({ first: firstMs, speech: kind === 'speech' ? firstMs : undefined }) } },
      onDone: () => { if (live() && talkRef.current !== 'listening') listen() },
    })
    queueRef.current = q
    const showFinal = (res: Ask) => {
      const answer = typeof res.answer === 'string' && res.answer ? res.answer : t('offline')
      setMsgs((m) => [...m, { role: 'bot', text: answer, res: { ...res, sources: Array.isArray(res.sources) ? res.sources : [] } }])
      const srv = (res as Ask & { timings?: { first_speak_ms?: number } }).timings?.first_speak_ms
      if (srv != null) setLat((l) => ({ first: l?.first ?? 0, ...l, server: srv }))
      return answer
    }
    const finish = (res: Ask) => {
      finished = res
      const answer = showFinal(res)
      if (!heard) { const say = (typeof res.speak === 'string' && res.speak.trim()) || speakFallback(answer); if (say) q.push(say) }
      q.close()
      if (!heard && !q.started() && !(typeof res.speak === 'string' && res.speak.trim()) && !speakFallback(answer)) listen()
    }
    try {
      void preloadFiller(langRef.current)
      fillerTimer = setTimeout(() => { fillerTimer = null; if (live() && !spoke) q.filler(langRef.current) }, 300)
      try {
        await api.askStream(text, langRef.current, placeRef.current, { history, signal: ac.signal }, (ev) => {
          if (!live()) return
          if (ev.type === 'speak') { heard = true; spoke = true; clearFiller(); q.push(ev.text) }
          else if (ev.type === 'final') { clearFiller(); finish(ev) }
          else if (ev.type === 'error') throw new ApiError(ev.detail || t('offline'), 500)
        })
      } catch (e) {
        if (e instanceof ApiError && e.status === 404 && live() && !finished) {
          const res = await api.ask(text, langRef.current, placeRef.current, { history, mode: 'voice', signal: ac.signal })
          if (live()) { clearFiller(); finish(res) }
        } else throw e
      }
      if (live() && !finished) { clearFiller(); q.close(); if (!q.started()) listen() }
    } catch (e) {
      clearFiller(); q.cancel(); stopSpeaking()
      if (!live()) return
      if (e instanceof ApiError && e.status === 429) { endTalk(t('p4.rate')); return }
      setMsgs((m) => [...m, { role: 'bot', text: t('p4.error'), error: true }])
      setTalk('paused')
    }
  }

  const talkTap = () => {
    if (!SpeechRec) { setTalkNote(t('talk.unsupported')); return }
    setTalkNote('')
    if (talkRef.current === 'thinking') return
    if (talkRef.current === 'listening') { pauseTalk(); return }
    // off, paused, or speaking (barge-in): stop any audio and listen
    unlockAudio()
    activeRef.current = true; silentRef.current = 0
    listen()
  }

  // language switched mid-conversation: restart the recognizer with the new lang
  const lastLang = useRef(lang)
  useEffect(() => {
    if (lastLang.current === lang) return
    lastLang.current = lang
    if (activeRef.current && talkRef.current === 'listening') listen()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  useEffect(() => {
    const onVis = () => { if (document.hidden && activeRef.current && talkRef.current !== 'paused') pauseTalk() }
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const send = async (text: string) => {
    if (!text.trim() || busy) return
    if (aloud) unlockAudio()
    setMsgs((m) => [...m, { role: 'user', text }]); setQ(''); setBusy(true)
    try {
      const res = await api.ask(text, lang, place)
      const answer = typeof res.answer === 'string' && res.answer ? res.answer : t('offline')
      setMsgs((m) => [...m, { role: 'bot', text: answer, res: { ...res, sources: Array.isArray(res.sources) ? res.sources : [] } }])
      if (aloud) { const say = (typeof res.speak === 'string' && res.speak.trim()) || speakFallback(answer); if (say) speak(say, lang, () => {}) }
    } catch (e) {
      setMsgs((m) => [...m, { role: 'bot', text: e instanceof ApiError && e.status === 429 ? t('p4.rate') : t('p4.error'), error: true }])
    } finally { setBusy(false) }
  }
  const retry = () => {
    const last = [...msgsRef.current].reverse().find((m) => m.role === 'user')
    if (last) { setMsgs((m) => m.filter((x) => !x.error)); void send(last.text) }
  }

  const mic = () => {
    if (!SpeechRec || activeRef.current) return
    const r = new SpeechRec()
    r.lang = LANGS.find((l) => l.code === lang)?.speech ?? 'en-US'
    r.onresult = (e) => { const s = e.results[0][0].transcript; setQ(s); send(s) }
    r.onend = () => setListening(false)
    r.onerror = () => setListening(false)
    setListening(true); r.start()
  }

  const say = (i: number, text: string) => {
    if (speakingIdx === i) { stopSpeaking(); setSpeakingIdx(null); return }
    setSpeakingIdx(i)
    speak(text, lang, () => setSpeakingIdx(null))
  }

  const orbState: OrbState = !SpeechRec ? 'error' : talk === 'listening' ? 'listening' : talk === 'thinking' ? 'thinking' : talk === 'speaking' ? 'speaking' : talk === 'paused' ? 'paused' : 'idle'
  const lastBot = [...msgs].map((m, i) => ({ m, i })).reverse().find((x) => x.m.role === 'bot')

  return (
    <div className="flex min-h-[60vh] flex-col">
      <PageHeader title={t('ask.title')} subtitle={t('ask.subtitle')} forPlace
        action={<IconButton icon={Settings2} label={t('p4.settings')} onClick={() => setSheet(true)} />} />
      <Segmented<AskMode> label={t('p4.mode')} value={mode} onChange={setMode} className="mb-4 md:max-w-xs"
        options={[{ value: 'type', label: t('p4.mode.type'), icon: Keyboard }, { value: 'talk', label: t('p4.mode.talk'), icon: Mic }]} />

      {mode === 'type' ? <>
        <div className="flex-1">
          {msgs.length === 0 && !busy
            ? <EmptyState icon={MessageCircleQuestion} title={t('p4.empty.title')} body={t('p4.empty.body')} action={<SuggestedQuestions onPick={(x) => send(x)} />} />
            : <MessageList msgs={msgs} busy={busy} speakingIdx={speakingIdx} onListen={say} onRetry={retry} />}
          <div ref={end} />
        </div>
        <Composer value={q} onChange={setQ} onSend={() => send(q)} busy={busy}
          micSupported={!!SpeechRec} micActive={listening} micDisabled={talk !== 'off'} onMic={mic} />
      </> : (
        <div className="flex flex-1 flex-col items-center gap-4">
          {engine === 'fast' ? <>
            <div className="pt-4">
              <VoiceOrb state={orbState} onPress={SpeechRec ? talkTap : () => setMode('type')} />
              {!SpeechRec && <div className="mt-3 flex justify-center"><Button variant="secondary" onClick={() => setMode('type')}>{t('p4.switchType')}</Button></div>}
            </div>
            {talkNote && talk === 'off' && <p role="status" className="text-center text-body-sm text-muted">{talkNote}</p>}
            {talk === 'listening' && interim && <p className="text-center text-[17px] text-ink">“{interim}”</p>}
            {lastBot && (
              <div className="w-full">
                <MessageList msgs={[lastBot.m]} speakingIdx={speakingIdx === lastBot.i ? 0 : null} onListen={(_, tx) => say(lastBot.i, tx)} />
              </div>
            )}
            {talk !== 'off' && <Button variant="ghost" onClick={() => endTalk()}>{t('p4.end')}</Button>}
            <DemoPanel title={t('p4.diag')}>
              <p data-testid="latency" className="text-body-sm text-ink">
                {lat ? `${t('p4.diag.first')} ${lat.first} ms${lat.speech != null ? '' : ` (${t('p4.diag.filler')})`}${lat.server != null ? ` · ${t('p4.diag.server')} ${lat.server} ms` : ''}` : '—'}
              </p>
            </DemoPanel>
          </> : (
            <div className="w-full pt-4">
              <Suspense fallback={<LoadingText />}>
                {engine === 'live' ? <LiveTalk lang={lang} lat={place?.lat} lon={place?.lon} onFallback={() => setEngineState('fast')} onType={() => setMode('type')} /> : <ElAgentTalk lang={lang} lat={place?.lat} lon={place?.lon} />}
              </Suspense>
            </div>
          )}
        </div>
      )}
      <VoiceSettingsSheet open={sheet} onClose={() => setSheet(false)} engine={engine} onEngine={setEngine} aloud={aloud} onAloud={setAloud} />
    </div>
  )
}
