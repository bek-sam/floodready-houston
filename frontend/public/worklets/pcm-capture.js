// Mic -> 16 kHz PCM16 mono in fixed 20 ms frames (320 samples). Posts {pcm: ArrayBuffer, rms: number}.
// Downsampling uses a box filter over each output period (cheap anti-alias for 44.1/48 kHz input).
const OUT_RATE = 16000
const FRAME = 320 // 20 ms at 16 kHz
class PcmCapture extends AudioWorkletProcessor {
  constructor() {
    super()
    this.ratio = sampleRate / OUT_RATE
    this.pos = 0
    this.acc = 0
    this.n = 0
    this.out = new Int16Array(FRAME)
    this.oi = 0
    this.sq = 0
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0]
    if (!ch) return true
    for (let i = 0; i < ch.length; i++) {
      this.acc += ch[i]
      this.n++
      this.pos += 1
      if (this.pos >= this.ratio) {
        this.pos -= this.ratio
        const v = Math.max(-1, Math.min(1, this.acc / this.n))
        this.acc = 0
        this.n = 0
        this.sq += v * v
        this.out[this.oi++] = v < 0 ? v * 0x8000 : v * 0x7fff
        if (this.oi === FRAME) {
          const buf = this.out.buffer
          this.port.postMessage({ pcm: buf, rms: Math.sqrt(this.sq / FRAME) }, [buf])
          this.out = new Int16Array(FRAME)
          this.oi = 0
          this.sq = 0
        }
      }
    }
    return true
  }
}
registerProcessor('pcm-capture', PcmCapture)
