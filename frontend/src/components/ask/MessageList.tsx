import { useState, type ReactNode } from 'react'
import { Copy, Square, ThumbsDown, ThumbsUp, Volume2 } from 'lucide-react'
import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'
import type { Ask } from '../../api'
import { Button, Disclosure, ErrorBox, IconButton, SourceLink } from '../ds'

export interface Msg { role: 'user' | 'bot'; text: string; res?: Ask; error?: boolean }

/** Light markdown: bullets, line breaks, [text](url) and bare URLs as links. */
export function Md({ text: raw, sources }: { text: string; sources?: string[] }) {
  const text = typeof raw === 'string' ? raw : ''
  const inline = (s: string) => s.split(/(\[[^\]]+\]\(https?:[^)]+\)|https?:\/\/[^\s\])]+|\*\*[^*]+\*\*|\[\d{1,2}\])/g).map((p, i) => {
    const c = p.match(/^\[(\d{1,2})\]$/)
    if (c) {
      const n = Number(c[1]), href = sources?.[n - 1]
      if (!href) return null
      let host = href
      try { host = new URL(href).hostname.replace(/^www\./, '') } catch { /* keep raw */ }
      return <sup key={i} className="ms-0.5"><a href={href} target="_blank" rel="noreferrer" aria-label={`Source ${n}: ${host}`} title={host}
        className="inline-flex min-w-4 items-center justify-center rounded bg-surface-2 px-1 text-[0.7rem] font-semibold text-brand no-underline hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1">{n}</a></sup>
    }
    const m = p.match(/^\[([^\]]+)\]\((https?:[^)]+)\)$/)
    if (m) return <a key={i} href={m[2]} target="_blank" rel="noreferrer" className="underline">{m[1]}</a>
    if (/^https?:/.test(p)) return <a key={i} href={p} target="_blank" rel="noreferrer" className="break-all underline">{p}</a>
    if (/^\*\*.+\*\*$/.test(p)) return <b key={i}>{p.slice(2, -2)}</b>
    return p
  })
  const out: ReactNode[] = []
  let items: string[] = []
  const flush = () => { if (items.length) { out.push(<ul key={out.length} className="my-1 list-disc space-y-1 ps-5">{items.map((x, i) => <li key={i}>{inline(x)}</li>)}</ul>); items = [] } }
  text.split('\n').forEach((line) => {
    const b = line.match(/^\s*[-*•]\s+(.*)/)
    if (b) items.push(b[1])
    else { flush(); if (line.trim()) out.push(<p key={out.length} className="my-1">{inline(line)}</p>) }
  })
  flush()
  return <div>{out}</div>
}

function Typing({ label }: { label: string }) {
  return (
    <div role="status" className="flex items-center gap-2 text-body-sm text-muted">
      <span aria-hidden className="flex gap-1">
        {[0, 1, 2].map((i) => <span key={i} className="size-2 rounded-full bg-muted motion-safe:animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}
      </span>
      {label}
    </div>
  )
}

function Sources({ list }: { list: string[] }) {
  const { t } = useApp()
  const [all, setAll] = useState(false)
  const shown = all ? list : list.slice(0, 3)
  return (
    <div className="text-caption">
      <span className="font-semibold text-muted">{t('p4.sources')}:</span>
      {shown.map((s) => <SourceLink key={s} href={s} />)}
      {list.length > 3 && (
        <button type="button" onClick={() => setAll(!all)} className="ms-2 min-h-6 font-semibold text-brand underline underline-offset-2">
          {all ? t('p4.fewerSources') : t('p4.moreSources').replace('{n}', String(list.length - 3))}
        </button>
      )}
    </div>
  )
}

/** Thumbs up/down under an answer -> POST /api/feedback. One vote per answer; failures are silent. */
function Feedback({ question, answer }: { question: string; answer: string }) {
  const { t, lang } = useApp()
  const tr = (k: string, d: string) => { const v = t(k); return v === k ? d : v }
  const [vote, setVote] = useState<1 | -1 | null>(null)
  const send = (rating: 1 | -1) => {
    if (vote !== null) return
    setVote(rating)
    fetch('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question.slice(0, 2000), answer: answer.slice(0, 8000), rating, lang }) }).catch(() => { /* ignore */ })
  }
  return (
    <div role="group" aria-label={tr('p4.feedback', 'Was this answer helpful?')} className="flex items-center">
      <IconButton icon={ThumbsUp} label={tr('p4.helpful', 'Helpful')} aria-pressed={vote === 1} disabled={vote !== null && vote !== 1}
        className={vote === 1 ? 'text-brand' : ''} onClick={() => send(1)} />
      <IconButton icon={ThumbsDown} label={tr('p4.notHelpful', 'Not helpful')} aria-pressed={vote === -1} disabled={vote !== null && vote !== -1}
        className={vote === -1 ? 'text-brand' : ''} onClick={() => send(-1)} />
      <span role="status" className="ms-1 text-caption text-muted">{vote !== null ? tr('p4.thanks', 'Thanks for the feedback') : ''}</span>
    </div>
  )
}

function Bot({ m, i, speakingIdx, onListen, question }: { m: Msg; i: number; speakingIdx: number | null; onListen: (i: number, text: string) => void; question: string }) {
  const { t } = useApp()
  const { demo } = useDemoMode()
  const [copied, setCopied] = useState(false)
  const res = m.res!
  const tools = Array.from(new Set(res.tools_used ?? res.tools ?? []))
  const name = (k: string) => { const v = t('p4.tool.' + k); return v === 'p4.tool.' + k ? k.replace(/^get_/, '').replace(/_/g, ' ') : v }
  const by = res.generated_by === 'gemini' ? t('p4.by.gemini') : res.generated_by === 'template' ? t('p4.by.template') : res.generated_by
  const copy = async () => { try { await navigator.clipboard.writeText(m.text); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* ignore */ } }
  return (
    <>
      <Md text={m.text} sources={res.sources} />
      <div className="mt-2 flex flex-wrap gap-1">
        <Button variant="ghost" size="sm" icon={speakingIdx === i ? Square : Volume2} aria-pressed={speakingIdx === i} onClick={() => onListen(i, m.text)}>
          {speakingIdx === i ? t('p4.stop') : t('p4.listen')}
        </Button>
        <Button variant="ghost" size="sm" icon={Copy} onClick={copy}>{copied ? t('p4.copied') : t('p4.copy')}</Button>
        <Feedback question={question} answer={m.text} />
      </div>
      {tools.length > 0 && (
        <p className="mt-1 flex flex-wrap items-center gap-1.5 text-caption text-muted">
          <span>{t('p4.used')}:</span>
          {tools.map((k) => <span key={k} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-ink">{name(k)}</span>)}
        </p>
      )}
      {res.sources.length > 0 && <div className="mt-2"><Sources list={res.sources} /></div>}
      <Disclosure className="mt-2 shadow-none" title={<span className="text-body-sm font-medium text-muted">{t('p4.how')}</span>}>
        <p className="text-body-sm text-muted">{by}</p>
        {demo && <p className="mt-1 text-caption text-muted">via {res.generated_by}{tools.length ? ` · ${tools.join(', ')}` : ''}</p>}
      </Disclosure>
    </>
  )
}

export function MessageList({ msgs, busy, speakingIdx, onListen, onRetry }: {
  msgs: Msg[]; busy?: boolean; speakingIdx: number | null; onListen: (i: number, text: string) => void; onRetry?: () => void
}) {
  const { t } = useApp()
  return (
    <div className="space-y-3" aria-live="polite">
      {msgs.map((m, i) => (
        <div key={i} className={m.role === 'user' ? 'flex justify-end' : ''}>
          <div className={`rounded-lg p-3 text-body ${m.role === 'user' ? 'max-w-[85%] bg-brand text-brandink' : 'w-full border border-line bg-surface md:max-w-[92%]'}`}>
            {m.error ? <ErrorBox error={m.text} onRetry={i === msgs.length - 1 ? onRetry : undefined} />
              : m.role === 'bot' && m.res ? <Bot m={m} i={i} speakingIdx={speakingIdx} onListen={onListen} question={msgs.slice(0, i).reverse().find((x) => x.role === 'user')?.text ?? ''} />
              : m.role === 'bot' ? <Md text={m.text} /> : <p>{m.text}</p>}
          </div>
        </div>
      ))}
      {busy && <div className="w-full rounded-lg border border-line bg-surface p-3"><Typing label={t('p4.checking')} /></div>}
    </div>
  )
}
