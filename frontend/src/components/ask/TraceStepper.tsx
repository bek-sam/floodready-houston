import type { AskTrace } from '../../api'
import { useApp } from '../../ctx'
import { Disclosure, SourceLink } from '../ds'

/** "How I answered": 4-step trace from /ask `trace`. Renders nothing when the backend sent none. */
export default function TraceStepper({ trace }: { trace?: AskTrace | null }) {
  const { t } = useApp()
  if (!trace || typeof trace !== 'object') return null
  const retrieved = (Array.isArray(trace.retrieved) ? trace.retrieved : []).filter((r) => r && r.title).slice(0, 3)
  const tools = (Array.isArray(trace.tools) ? trace.tools : []).filter((x) => x && x.name)
  const by = trace.answer?.by
  const tool = (k: string) => { const v = t('p4.tool.' + k); return v === 'p4.tool.' + k ? k.replace(/^get_/, '').replace(/_/g, ' ') : v }
  const steps: { h: string; body: React.ReactNode }[] = [
    { h: t('p32.trace.understand'), body: <span>{trace.intent ? trace.intent.replace(/_/g, ' ') : '—'}{trace.route === 'cache' && ` · ${t('p32.trace.cache')}`}</span> },
    { h: t('p32.trace.search'), body: retrieved.length ? (
      <ul className="space-y-0.5">{retrieved.map((r, i) => <li key={i}>{/^https?:/.test(r.source) ? <SourceLink href={r.source} label={r.title} /> : r.title}</li>)}</ul>
    ) : <span>{t('p32.trace.none')}</span> },
    { h: t('p32.trace.live'), body: tools.length ? (
      <ul className="flex flex-wrap gap-1.5">{tools.map((x, i) => <li key={i} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-ink">{tool(x.name)}{typeof x.ms === 'number' && (x.ms < 5 ? ` · ${t('p32.trace.cached')}` : ` · ${Math.round(x.ms)} ms`)}</li>)}</ul>
    ) : <span>{t('p32.trace.none')}</span> },
    { h: t('p32.trace.write'), body: <span>
      {by === 'template' ? <span className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-ink">{t('p32.trace.template')}</span> : by === 'gemini' ? 'Gemini' : by ?? '—'}
      {typeof trace.answer?.ms === 'number' && ` · ${Math.round(trace.answer.ms)} ms`}
      {typeof trace.total_ms === 'number' && ` · ${t('p32.trace.total')} ${Math.round(trace.total_ms)} ms`}</span> },
  ]
  return (
    <Disclosure className="mt-2 shadow-none" title={<span className="text-body-sm font-medium text-muted">{t('p32.trace.title')}</span>}>
      <ol className="space-y-2 text-body-sm text-muted">
        {steps.map((s, i) => (
          <li key={i} className="flex gap-2">
            <span aria-hidden className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-brand text-caption font-semibold text-brandink">{i + 1}</span>
            <div className="min-w-0"><p className="font-semibold text-ink">{s.h}</p><div>{s.body}</div></div>
          </li>
        ))}
      </ol>
      <p className="mt-2 text-caption text-muted">{t('p32.trace.note')}</p>
    </Disclosure>
  )
}
