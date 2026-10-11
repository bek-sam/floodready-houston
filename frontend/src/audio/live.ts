// Gemini Live client engine (Voice v2, see CLAUDE.md): full duplex.
// mic -> 16 kHz PCM16 in 20 ms frames over WS; WS -> 24 kHz PCM16 into a ring-buffer worklet.
// No client-side echo gating: we rely on getUserMedia AEC/NS/AGC plus server barge-in ("interrupted").
// All v2 server events are optional; older servers only send transcript/tool/interrupted/error.

export type Role = 'user' | 'model'
export type LiveEvent =
  | { type: 'transcript'; role: Role; text: string }
  | { type: 'caption'; role: Role; text: string; final?: boolean }
  | { type: 'tool'; name: string }
  | { type: 'thinking'; label?: string }
  | { type: 'turn'; event: 'user_end' | 'model_start' | 'model_end'; t?: number }
  | { type: 'ready'; model?: string; latency_hint?: number }
  | { type: 'resume'; handle: string }
  | { type: 'interrupted' }
  | { type: 'error'; detail: string }
  // Synthesized by the client:
  | { type: 'latency'; ms: number; source: 'server' | 'client' }
  | { type: 'playing'; on: boolean }
  | { type: 'reconnecting' }
  | { type: 'reconnected' }

export interface LiveOptions {
  lang: string
  lat?: number
  lon?: number
  place?: string
  /** base64 JSON household profile */
  profile?: string
  resume?: string
}

export interface LiveHandlers {
  onEvent: (e: LiveEvent) => void
  /** Session over. failed=true when it ended because of a connection problem (after one reconnect attempt). */
  onClose: (info: { failed: boolean }) => void
}

export const CONNECT_TIMEOUT_MS = 6000
export const RESUME_KEY = 'floodready.live.resume'
const VAD_RMS = 0.015 // 16 kHz frame RMS that counts as user speech (client fallback timing only)
const NEW_RESPONSE_GAP_MS = 700 // model audio after this much silence starts a new response

export function loadResume(): string | undefined {
  try { return sessionStorage.getItem(RESUME_KEY) || undefined } catch { return undefined }
}
function saveResume(h: string | null) {
  try { if (h) sessionStorage.setItem(RESUME_KEY, h); else sessionStorage.removeItem(RESUME_KEY) } catch { /* ignore */ }
}

/** UTF-8 safe base64 of a JSON value. */
export function b64json(v: unknown): string {
  const bytes = new TextEncoder().encode(JSON.stringify(v))
  let s = ''
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s)
}

function rmsOf(a: AnalyserNode | undefined, buf: Float32Array<ArrayBuffer> | undefined): number {
  if (!a || !buf) return 0
  a.getFloatTimeDomainData(buf)
  let s = 0
  for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i]
  return Math.sqrt(s / buf.length)
}

export class LiveSession {
  private ws?: WebSocket
  private stream?: MediaStream
  private capCtx?: AudioContext
  private playCtx?: AudioContext
  private player?: AudioWorkletNode
  private micAn?: AnalyserNode
  private outAn?: AnalyserNode
  private micBuf?: Float32Array<ArrayBuffer>
  private outBuf?: Float32Array<ArrayBuffer>
  private closed = false
  private ready = false
  private reconnects = 1
  private opts!: LiveOptions
  private muted = false
  private ptt = false
  // latency bookkeeping
  private userEndT: number | null = null
  private serverTurns = false
  private lastVoiceAt = 0
  private lastAudioAt = 0
  private h: LiveHandlers
  constructor(h: LiveHandlers) { this.h = h }

  /** Current 0..1 levels for the orb (mic input after AEC, assistant output). Cheap; call from rAF. */
  levels(): { mic: number; out: number } {
    const mic = this.muted && !this.ptt ? 0 : rmsOf(this.micAn, this.micBuf)
    return { mic: Math.min(1, mic * 6), out: Math.min(1, rmsOf(this.outAn, this.outBuf) * 5) }
  }

  async start(opts: LiveOptions) {
    this.opts = opts
    // Create + resume contexts synchronously, before any await, so it stays inside the click gesture (iOS/Safari).
    this.capCtx = new AudioContext({ latencyHint: 'interactive' })
    this.playCtx = new AudioContext({ sampleRate: 24000, latencyHint: 'interactive' })
    const resumed = Promise.all([this.capCtx.resume(), this.playCtx.resume()])
    resumed.catch(() => {})

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
    })
    await Promise.all([
      this.capCtx.audioWorklet.addModule('/worklets/pcm-capture.js'),
      this.playCtx.audioWorklet.addModule('/worklets/pcm-player.js'),
    ])
    await resumed.catch(() => {})
    if (this.capCtx.state === 'suspended') await this.capCtx.resume().catch(() => {})
    if (this.playCtx.state === 'suspended') await this.playCtx.resume().catch(() => {})
    if (this.closed) throw new Error('stopped')

    // Output: player -> analyser -> speakers
    this.player = new AudioWorkletNode(this.playCtx, 'pcm-player', { processorOptions: { jitterMs: 80 } })
    this.outAn = this.playCtx.createAnalyser(); this.outAn.fftSize = 512
    this.outBuf = new Float32Array(this.outAn.fftSize)
    this.player.connect(this.outAn); this.outAn.connect(this.playCtx.destination)
    this.player.port.onmessage = (e) => { if (typeof e.data?.playing === 'boolean') this.h.onEvent({ type: 'playing', on: e.data.playing }) }

    await this.open(opts.resume)

    // Input: mic -> analyser (orb) + capture worklet (20 ms frames -> WS)
    const src = this.capCtx.createMediaStreamSource(this.stream)
    this.micAn = this.capCtx.createAnalyser(); this.micAn.fftSize = 512
    this.micBuf = new Float32Array(this.micAn.fftSize)
    src.connect(this.micAn)
    const cap = new AudioWorkletNode(this.capCtx, 'pcm-capture', { numberOfOutputs: 0 })
    cap.port.onmessage = (e) => this.onFrame(e.data.pcm as ArrayBuffer, e.data.rms as number)
    src.connect(cap)
  }

  private url(resume?: string) {
    const o = this.opts
    const p = new URLSearchParams({ lang: o.lang })
    if (o.lat != null) p.set('lat', String(o.lat))
    if (o.lon != null) p.set('lon', String(o.lon))
    if (o.place) p.set('place', o.place)
    if (o.profile) p.set('profile', o.profile)
    if (resume) p.set('resume', resume)
    return `${location.origin.replace(/^http/, 'ws')}/api/live?${p}`
  }

  private async open(resume?: string) {
    let ws: WebSocket
    try { ws = await this.connect(this.url(resume)) }
    catch (e) {
      if (this.closed) throw e
      ws = await this.connect(this.url(resume)) // one quick retry for the initial handshake
    }
    if (this.closed) { try { ws.close() } catch { /* ignore */ } throw new Error('stopped') }
    this.attach(ws)
  }

  private attach(ws: WebSocket) {
    this.ws = ws
    let got = false
    ws.onmessage = (m) => {
      got = true
      if (typeof m.data === 'string') {
        let e: LiveEvent
        try { e = JSON.parse(m.data) as LiveEvent } catch { return }
        this.onServerEvent(e)
      } else this.onAudio(m.data as ArrayBuffer)
    }
    ws.onerror = () => { /* onclose follows */ }
    ws.onclose = () => {
      if (this.closed || this.ws !== ws) return
      // Server ended cleanly before anything happened, or the network dropped: try to resume once.
      if (this.reconnects > 0 && (this.ready || got)) { void this.reconnect(); return }
      this.teardown()
      this.h.onClose({ failed: true })
    }
    if (ws.readyState !== WebSocket.OPEN) throw new Error('Live voice disconnected before it started.')
    // Mute/PTT state survives a reconnect.
    if (this.muted) this.send({ type: 'mute', on: true })
  }

  private async reconnect() {
    this.reconnects--
    this.ready = false
    this.player?.port.postMessage({ flush: true })
    this.h.onEvent({ type: 'reconnecting' })
    try {
      await this.open(loadResume())
      this.h.onEvent({ type: 'reconnected' })
    } catch {
      if (this.closed) return
      this.teardown()
      this.h.onClose({ failed: true })
    }
  }

  private onServerEvent(e: LiveEvent) {
    switch (e.type) {
      case 'ready': this.ready = true; break
      case 'resume': if (e.handle) saveResume(e.handle); break
      case 'interrupted': this.flushPlayback(); break
      case 'turn':
        this.serverTurns = true
        if (e.event === 'user_end') { this.userEndT = typeof e.t === 'number' ? e.t : performance.now() }
        else if (e.event === 'model_start' && this.userEndT != null) {
          const t = typeof e.t === 'number' ? e.t : performance.now()
          const ms = t - this.userEndT
          if (ms >= 0 && ms < 30000) this.h.onEvent({ type: 'latency', ms, source: 'server' })
          this.userEndT = null
        }
        break
    }
    // Any server message means the session is up (older servers never send "ready").
    if (e.type !== 'error') this.ready = true
    this.h.onEvent(e)
  }

  private onAudio(buf: ArrayBuffer) {
    this.ready = true
    const now = performance.now()
    // Client-side fallback latency: last mic speech frame -> first audio of a new response.
    if (!this.serverTurns && now - this.lastAudioAt > NEW_RESPONSE_GAP_MS && this.lastVoiceAt > this.lastAudioAt) {
      const ms = now - this.lastVoiceAt
      if (ms > 0 && ms < 30000) this.h.onEvent({ type: 'latency', ms, source: 'client' })
    }
    this.lastAudioAt = now
    this.player?.port.postMessage({ pcm: buf }, [buf])
  }

  private onFrame(pcm: ArrayBuffer, rms: number) {
    const live = !this.muted || this.ptt
    if (live && rms > VAD_RMS) this.lastVoiceAt = performance.now()
    if (!live) return
    const ws = this.ws
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(pcm)
  }

  /** Stop assistant audio now (30 ms fade inside the worklet). */
  flushPlayback() { this.player?.port.postMessage({ flush: true }) }

  setMuted(on: boolean) {
    this.muted = on
    this.send({ type: 'mute', on })
  }

  /** Push-to-talk: manual activity start/end. Holding also unmutes and cuts off the assistant. */
  setPtt(down: boolean) {
    if (this.ptt === down) return
    this.ptt = down
    if (down) this.flushPlayback()
    this.send({ type: 'ptt', down })
  }

  private send(o: unknown) {
    try { if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(o)) } catch { /* ignore */ }
  }

  private connect(url: string): Promise<WebSocket> {
    return new Promise<WebSocket>((res, rej) => {
      const ws = new WebSocket(url)
      ws.binaryType = 'arraybuffer'
      let done = false
      const fail = (msg: string) => {
        if (done) return
        done = true; clearTimeout(timer)
        ws.onopen = ws.onerror = ws.onclose = null
        try { ws.close() } catch { /* ignore */ }
        rej(new Error(msg))
      }
      const timer = setTimeout(() => fail('timeout'), CONNECT_TIMEOUT_MS)
      ws.onopen = () => { if (done) return; done = true; clearTimeout(timer); res(ws) }
      ws.onerror = () => fail('Could not reach the live voice service.')
      ws.onclose = () => fail('Live voice closed before connecting.')
    })
  }

  /** User ended the conversation. */
  stop() {
    this.send({ type: 'end' })
    saveResume(null)
    this.teardown()
  }

  private teardown() {
    if (this.closed) return
    this.closed = true
    this.stream?.getTracks().forEach((t) => t.stop())
    this.player?.port.postMessage({ flush: true })
    this.capCtx?.close().catch(() => {})
    this.playCtx?.close().catch(() => {})
    const ws = this.ws
    this.ws = undefined
    if (ws) { ws.onclose = null; try { ws.close() } catch { /* ignore */ } }
  }
}
