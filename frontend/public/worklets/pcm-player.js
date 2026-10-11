// Low-latency PCM16 player: single ring buffer + ~80 ms jitter buffer.
// In:  {pcm: ArrayBuffer} | {flush: true}
// Out: {playing: boolean} when playback starts / drains.
// flush fades the current audio out over 30 ms starting in the next render quantum, then drops
// everything that was queued before the flush (audio that arrives after the flush is kept).
const CAP_SECONDS = 30
class PcmPlayer extends AudioWorkletProcessor {
  constructor(opts) {
    super()
    const o = (opts && opts.processorOptions) || {}
    this.cap = Math.round(sampleRate * CAP_SECONDS)
    this.buf = new Float32Array(this.cap)
    this.r = 0 // absolute read index
    this.w = 0 // absolute write index
    this.min = Math.round(sampleRate * (o.jitterMs || 80) / 1000)
    this.fadeLen = Math.round(sampleRate * 0.03)
    this.fade = 0 // samples left in the current fade-out
    this.cut = -1 // absolute index to jump to when the fade finishes
    this.playing = false
    this.lastWrite = 0
    this.port.onmessage = (e) => {
      const d = e.data
      if (d.flush) {
        if (this.playing && this.w > this.r) { this.fade = this.fadeLen; this.cut = this.w }
        else { this.r = this.w; this.fade = 0; this.cut = -1; this.setPlaying(false) }
        return
      }
      if (!d.pcm) return
      const i16 = new Int16Array(d.pcm)
      // Drop the oldest audio if the ring would overflow (never happens in practice: 30 s capacity).
      if (this.w + i16.length - this.r > this.cap) this.r = this.w + i16.length - this.cap
      for (let i = 0; i < i16.length; i++) this.buf[(this.w + i) % this.cap] = i16[i] / 32768
      this.w += i16.length
      this.lastWrite = currentFrame
    }
  }
  setPlaying(v) { if (v !== this.playing) { this.playing = v; this.port.postMessage({ playing: v }) } }
  process(_, outputs) {
    const out = outputs[0][0]
    if (!out) return true
    if (this.fade > 0) {
      for (let i = 0; i < out.length; i++) {
        if (this.fade > 0 && this.r < this.cut) {
          out[i] = this.buf[this.r % this.cap] * (this.fade / this.fadeLen)
          this.r++
        } else out[i] = 0
        if (this.fade > 0) this.fade--
      }
      if (this.fade <= 0 || this.r >= this.cut) {
        this.r = Math.max(this.r, this.cut); this.fade = 0; this.cut = -1
        this.setPlaying(false)
      }
      return true
    }
    if (!this.playing) {
      const n = this.w - this.r
      // Start once the jitter buffer is full, or play a short tail if no more audio is coming.
      if (n >= this.min || (n > 0 && currentFrame - this.lastWrite > this.min)) this.setPlaying(true)
      else { out.fill(0); return true }
    }
    for (let i = 0; i < out.length; i++) {
      if (this.r < this.w) { out[i] = this.buf[this.r % this.cap]; this.r++ }
      else out[i] = 0
    }
    if (this.r >= this.w) this.setPlaying(false) // underrun or end of turn: re-buffer before resuming
    return true
  }
}
registerProcessor('pcm-player', PcmPlayer)
