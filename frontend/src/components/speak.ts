import { api } from '../api'
import { LANGS } from '../i18n'

// One shared element: once unlocked by a user gesture (iOS/Safari), later src swaps may autoplay.
let audio: HTMLAudioElement | null = null
let curUrl: string | null = null
let token = 0
const SILENT = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='

function revoke() { if (curUrl) { URL.revokeObjectURL(curUrl); curUrl = null } }

/** Call synchronously inside a user gesture (e.g. the Talk tap) so later async playback is allowed. */
export function unlockAudio() {
  try {
    if (!audio) audio = new Audio()
    audio.src = SILENT
    void audio.play().catch(() => { /* ignore */ })
  } catch { /* ignore */ }
  try {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(' '); u.volume = 0
      window.speechSynthesis.speak(u)
    }
  } catch { /* ignore */ }
}

export function stopSpeaking() {
  token++
  if (audio) { audio.onended = null; audio.onerror = null; try { audio.pause() } catch { /* ignore */ } }
  revoke()
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

/** Try /api/voice (ElevenLabs); fall back to browser speechSynthesis on any failure. onEnd fires once. */
export async function speak(text: string, lang: string, onEnd?: () => void) {
  stopSpeaking()
  const my = token
  let done = false
  const finish = () => { if (done || my !== token) return; done = true; onEnd?.() }
  try {
    const blob = await api.voice(text, lang)
    if (my !== token) return
    if (!audio) audio = new Audio()
    const a = audio
    revoke()
    curUrl = URL.createObjectURL(blob)
    a.onended = () => { revoke(); finish() }
    a.onerror = () => { revoke(); finish() }
    a.src = curUrl
    await a.play()
    return
  } catch {
    if (my !== token) return
    if (audio) { audio.onended = null; audio.onerror = null }
    revoke()
  }
  if ('speechSynthesis' in window) {
    const u = new SpeechSynthesisUtterance(text)
    u.lang = LANGS.find((l) => l.code === lang)?.speech ?? 'en-US'
    u.onend = finish
    u.onerror = finish
    window.speechSynthesis.speak(u)
  } else finish()
}

const fillerCache = new Map<string, Promise<Blob | null>>()
/** Preload + cache the localized "one moment" filler clip. */
export function preloadFiller(lang: string): Promise<Blob | null> {
  let p = fillerCache.get(lang)
  if (!p) { p = api.filler(lang).catch(() => { fillerCache.delete(lang); return null }); fillerCache.set(lang, p) }
  return p
}

export interface SpeechQueue {
  push: (text: string) => void
  filler: (lang: string) => void
  /** No more sentences coming; onDone fires after the queue drains. */
  close: () => void
  cancel: () => void
  started: () => boolean
}

/** Sentence pipeline: audio for N+1.. is fetched while N plays. Falls back to speechSynthesis per sentence. */
export function createSpeechQueue(lang: string, opts: { onFirstAudio?: (kind: 'filler' | 'speech') => void; onDone?: () => void }): SpeechQueue {
  stopSpeaking()
  const my = token
  const ac = new AbortController()
  type Item = { text: string; blob: Promise<Blob | null>; filler?: boolean }
  const items: Item[] = []
  let running = false, closed = false, fired = false, firstSpeech = false, doneFired = false
  const alive = () => my === token
  const fireDone = () => { if (doneFired || !alive()) return; doneFired = true; opts.onDone?.() }

  const playBlob = (b: Blob, kind: 'filler' | 'speech') => new Promise<boolean>((resolve) => {
    if (!audio) audio = new Audio()
    const a = audio
    revoke(); curUrl = URL.createObjectURL(b)
    const end = (ok: boolean) => { a.onended = null; a.onerror = null; revoke(); resolve(ok) }
    a.onended = () => end(true); a.onerror = () => end(false)
    a.src = curUrl
    a.play().then(() => { if (!fired) { fired = true; opts.onFirstAudio?.(kind) } else if (kind === 'speech' && !firstSpeech) { /* noop */ } }).catch(() => end(false))
  })
  const playTts = (text: string) => new Promise<void>((resolve) => {
    if (!('speechSynthesis' in window)) { resolve(); return }
    const u = new SpeechSynthesisUtterance(text)
    u.lang = LANGS.find((l) => l.code === lang)?.speech ?? 'en-US'
    u.onend = () => resolve(); u.onerror = () => resolve()
    if (!fired) { fired = true; opts.onFirstAudio?.('speech') }
    window.speechSynthesis.speak(u)
  })

  const run = async () => {
    if (running) return
    running = true
    while (alive()) {
      const it = items.shift()
      if (!it) { if (closed) fireDone(); break }
      const b = await it.blob
      if (!alive()) break
      if (it.filler) { if (b) await playBlob(b, 'filler'); continue }
      firstSpeech = true
      if (!(b && await playBlob(b, 'speech'))) { if (!alive()) break; await playTts(it.text) }
    }
    running = false
    if (alive() && items.length) void run()
  }

  return {
    push(text) {
      if (!alive() || !text.trim()) return
      items.push({ text, blob: api.voiceSentence(text, lang, ac.signal).catch(() => null) })
      void run()
    },
    filler(l) {
      if (!alive() || firstSpeech || items.length) return
      items.push({ text: '', filler: true, blob: preloadFiller(l) })
      void run()
    },
    close() { closed = true; if (!running) { if (items.length) void run(); else fireDone() } },
    cancel() { ac.abort(); items.length = 0; closed = true },
    started: () => fired,
  }
}
