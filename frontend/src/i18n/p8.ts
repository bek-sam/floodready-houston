// P8 strings: Voice v2 (full-screen voice mode). en is the reference; es keeps parity.
// Also renames the engines: Live -> "Voice" (default), Standard -> "Voice (compatibility)".
type Dict = Record<string, string>
export const en: Dict = {
  'p4.set.live': 'Voice', 'p4.set.live.d': 'Natural back-and-forth conversation. Talk any time, even while it answers.',
  'p4.set.standard': 'Voice (compatibility)', 'p4.set.standard.d': 'Use this if Voice does not work on your network or browser.',
  'p8.dialog': 'Voice conversation', 'p8.title': 'Voice',
  'p8.start': 'Tap to start a voice conversation', 'p8.start.hint': 'Talk naturally. You can interrupt at any time.',
  'p8.state.connecting': 'Connecting…', 'p8.state.reconnecting': 'Reconnecting…',
  'p8.state.listening': 'Listening', 'p8.state.user': 'Hearing you…', 'p8.state.thinking': 'Thinking…',
  'p8.state.speaking': 'Speaking. Just talk to interrupt.', 'p8.state.muted': 'Microphone is off',
  'p8.thinking.default': 'Checking sources',
  'p8.captions': 'Captions', 'p8.captions.empty': 'Say something like “Is my street likely to flood?”',
  'p8.mute': 'Mute microphone', 'p8.unmute': 'Unmute microphone',
  'p8.ptt': 'Hold to talk', 'p8.ptt.hint': 'or hold the space bar',
  'p8.end': 'End', 'p8.endLabel': 'End voice conversation', 'p8.type': 'Switch to typing',
  'p8.latency': 'Response time: {s} s',
  'p8.fallback': 'Voice could not connect, so we switched to Voice (compatibility).',
  'p8.ended': 'Conversation ended.', 'p8.recent': 'Last conversation',
}
export const es: Dict = {
  'p4.set.live': 'Voz', 'p4.set.live.d': 'Conversación natural. Hable cuando quiera, incluso mientras responde.',
  'p4.set.standard': 'Voz (compatibilidad)', 'p4.set.standard.d': 'Use esta opción si Voz no funciona en su red o navegador.',
  'p8.dialog': 'Conversación por voz', 'p8.title': 'Voz',
  'p8.start': 'Toque para iniciar una conversación por voz', 'p8.start.hint': 'Hable con naturalidad. Puede interrumpir en cualquier momento.',
  'p8.state.connecting': 'Conectando…', 'p8.state.reconnecting': 'Reconectando…',
  'p8.state.listening': 'Escuchando', 'p8.state.user': 'Le escucho…', 'p8.state.thinking': 'Pensando…',
  'p8.state.speaking': 'Hablando. Hable para interrumpir.', 'p8.state.muted': 'El micrófono está apagado',
  'p8.thinking.default': 'Revisando fuentes',
  'p8.captions': 'Subtítulos', 'p8.captions.empty': 'Diga algo como “¿Es probable que mi calle se inunde?”',
  'p8.mute': 'Silenciar micrófono', 'p8.unmute': 'Activar micrófono',
  'p8.ptt': 'Mantenga para hablar', 'p8.ptt.hint': 'o mantenga la barra espaciadora',
  'p8.end': 'Terminar', 'p8.endLabel': 'Terminar la conversación por voz', 'p8.type': 'Cambiar a escribir',
  'p8.latency': 'Tiempo de respuesta: {s} s',
  'p8.fallback': 'Voz no pudo conectarse, así que cambiamos a Voz (compatibilidad).',
  'p8.ended': 'Conversación terminada.', 'p8.recent': 'Última conversación',
}
// Engine names for the other languages (the rest falls back to en).
export const vi: Dict = { 'p4.set.live': 'Giọng nói', 'p4.set.standard': 'Giọng nói (tương thích)' }
export const zh: Dict = { 'p4.set.live': '语音', 'p4.set.standard': '语音（兼容模式）' }
export const ar: Dict = { 'p4.set.live': 'الصوت', 'p4.set.standard': 'الصوت (وضع التوافق)' }
