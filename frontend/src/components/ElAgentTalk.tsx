import { useEffect, useRef, useState } from 'react'
import { Conversation } from '@elevenlabs/client'
import { api } from '../api'
import { useApp } from '../ctx'
import { VoiceOrb, type OrbState } from './ask/VoiceOrb'

type Msg = { id: number; role: 'user' | 'agent'; text: string }
type Loc = { lat: number; lon: number }

const compact = (v: unknown) => { try { return JSON.stringify(v).slice(0, 4000) } catch { return '{}' } }
async function getJson(path: string) {
  const r = await fetch('/api' + path)
  if (!r.ok) throw new Error(String(r.status))
  return compact(await r.json())
}
const safe = (f: () => Promise<string>) => async () => { try { return await f() } catch { return compact({ error: 'unavailable' }) } }

export default function ElAgentTalk({ lang, lat, lon }: { lang: string; lat?: number; lon?: number }) {
  const { t } = useApp()
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected'>('idle')
  const [mode, setMode] = useState<'listening' | 'speaking'>('listening')
  const [err, setErr] = useState('')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const conv = useRef<{ endSession: () => Promise<void> } | null>(null)
  const id = useRef(0)

  useEffect(() => () => { conv.current?.endSession().catch(() => {}) }, [])

  async function start() {
    setErr(''); setMsgs([]); setStatus('connecting')
    try {
      const r = await fetch('/api/el-agent/signed-url')
      if (r.status === 503) throw new Error(t('p4.el.unconfigured'))
      if (!r.ok) throw new Error(t('p4.el.fail'))
      const { signed_url } = await r.json()
      if (!signed_url) throw new Error(t('p4.el.unconfigured'))
      await navigator.mediaDevices.getUserMedia({ audio: true }).then((s) => s.getTracks().forEach((t) => t.stop()))

      const loc = (p?: { lat?: number; lon?: number }): Loc | null => {
        const la = Number(p?.lat ?? lat), lo = Number(p?.lon ?? lon)
        return Number.isFinite(la) && Number.isFinite(lo) ? { lat: la, lon: lo } : null
      }
      const withLoc = (p: { lat?: number; lon?: number } | undefined, f: (l: Loc) => Promise<string>) =>
        safe(async () => { const l = loc(p); return l ? f(l) : compact({ error: 'no location set' }) })()
      const qs = (l: Loc) => `lat=${l.lat}&lon=${l.lon}`

      const c = await Conversation.startSession({
        signedUrl: signed_url,
        clientTools: {
          get_risk: (p: { lat?: number; lon?: number }) => withLoc(p, (l) => getJson('/risk?' + qs(l))),
          get_flood_history: (p: { lat?: number; lon?: number; zip?: string }) =>
            withLoc(p, (l) => getJson('/flood-history?' + qs(l) + (p?.zip ? '&zip=' + encodeURIComponent(p.zip) : ''))),
          get_zip_insurance: (p: { zip: string }) => safe(() => getJson('/zip-insurance?zip=' + encodeURIComponent(p?.zip ?? '')))(),
          get_alerts: (p: { lat?: number; lon?: number }) => withLoc(p, (l) => getJson('/alerts?' + qs(l))),
          get_medical: (p: { lat?: number; lon?: number }) => withLoc(p, (l) => getJson('/medical?' + qs(l) + '&kind=dialysis&limit=5')),
          search_knowledge: (p: { question?: string; query?: string }) => safe(async () => {
            const a = await api.ask(p?.question ?? p?.query ?? '', lang, loc(p as Loc), { mode: 'voice' })
            return a.answer
          })(),
        },
        onStatusChange: ({ status: s }) => {
          if (s === 'connected') setStatus('connected')
          else if (s === 'connecting') setStatus('connecting')
          else { setStatus('idle'); conv.current = null }
        },
        onModeChange: ({ mode: m }) => setMode(m),
        onMessage: (m) => {
          const role = (m as { role?: string }).role === 'user' || m.source === 'user' ? 'user' : 'agent'
          setMsgs((p) => [...p, { id: ++id.current, role, text: m.message }])
        },
        onError: (m) => setErr(m || t('p4.el.fail')),
      })
      conv.current = c
    } catch (e) {
      setStatus('idle')
      const n = (e as { name?: string })?.name
      setErr(n === 'NotAllowedError' ? t('p4.live.denied') : (e as Error).message || t('p4.el.fail'))
    }
  }
  async function stop() {
    const c = conv.current; conv.current = null
    setStatus('idle')
    try { await c?.endSession() } catch { /* ignore */ }
  }

  const state: OrbState = status === 'connecting' ? 'thinking' : status === 'idle' ? 'idle' : mode === 'speaking' ? 'speaking' : 'listening'
  return (
    <section aria-label={t('p4.set.el')} className="space-y-4">
      <VoiceOrb state={state} onPress={status === 'idle' ? start : stop} disabled={status === 'connecting'} />
      {err && <p role="alert" className="text-center text-body-sm text-danger">{err}</p>}
      <div role="log" aria-live="polite" aria-label={t('p4.live.log')} className="max-h-72 space-y-2 overflow-y-auto">
        {msgs.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex'}>
            <p className={'max-w-[85%] rounded-lg px-3 py-2 text-body ' + (m.role === 'user' ? 'bg-brand text-brandink' : 'border border-line bg-surface text-ink')}>
              <span className="sr-only">{m.role === 'user' ? t('p4.live.you') : t('p4.live.assistant')}: </span>{m.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
