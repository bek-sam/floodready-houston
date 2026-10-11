import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'

type Msg = { from: 'me' | 'bot'; text: string }
const SIM_PHONE = '+15555550100'
const QUICK = ['77096', 'AYUDA 77096', 'ALERTS ON 77096', 'HELP', 'STOP']

// Phone-like chat for the SMS channel (no Twilio, no real texts): POST /api/sms/simulate.
export default function SmsSimulator() {
  const [msgs, setMsgs] = useState<Msg[]>([{ from: 'bot', text: 'Text a Houston ZIP or street address to FloodReady. Try 77096 or AYUDA 77096.' }])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView?.({ block: 'nearest' }) }, [msgs])

  const send = async (body: string) => {
    const b = body.trim()
    if (!b || busy) return
    setText(''); setBusy(true)
    setMsgs((m) => [...m, { from: 'me', text: b }])
    try {
      const res = await fetch('/api/sms/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ from: SIM_PHONE, body: b }) })
      if (!res.ok) throw new Error(String(res.status))
      const { reply } = await res.json() as { reply: string }
      setMsgs((m) => [...m, { from: 'bot', text: reply || '(no reply: you are unsubscribed, text START)' }])
    } catch {
      setMsgs((m) => [...m, { from: 'bot', text: 'Could not reach FloodReady. Call 911 if in danger.' }])
    } finally { setBusy(false) }
  }

  return (
    <div className="mx-auto w-full max-w-xs rounded-[2rem] border-4 border-ink bg-surface p-2 shadow-md">
      <div className="py-1 text-center text-caption font-semibold text-muted">FloodReady SMS</div>
      <div role="log" aria-live="polite" aria-label="SMS conversation" className="h-72 space-y-2 overflow-y-auto rounded-xl bg-brand-tint/40 p-2">
        {msgs.map((m, i) => (
          <div key={i} className={m.from === 'me' ? 'flex justify-end' : 'flex justify-start'}>
            <p className={'max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-body-sm ' + (m.from === 'me' ? 'bg-brand text-white' : 'bg-white text-ink')}>{m.text}</p>
          </div>
        ))}
        {busy && <p className="text-caption text-muted">...</p>}
        <div ref={end} />
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {QUICK.map((q) => <button key={q} type="button" onClick={() => send(q)} className="rounded-full border border-line px-2 py-0.5 text-caption text-ink">{q}</button>)}
      </div>
      <form className="mt-2 flex gap-1" onSubmit={(e) => { e.preventDefault(); send(text) }}>
        <input value={text} onChange={(e) => setText(e.target.value)} aria-label="Text message" placeholder="ZIP or address" maxLength={300}
          className="min-w-0 flex-1 rounded-full border border-line bg-white px-3 py-2 text-body-sm text-ink" />
        <button type="submit" disabled={busy} aria-label="Send" className="flex size-10 items-center justify-center rounded-full bg-brand text-white"><Send size={16} /></button>
      </form>
    </div>
  )
}
