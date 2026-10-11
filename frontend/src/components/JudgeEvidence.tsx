import { useEffect, useState } from 'react'
import { useApp } from '../ctx'
import { Card } from './ds'

type Item = { id: string; label: string; value: string; detail?: string; as_of?: string; source_path?: string; source_url?: string }
type Stats = { n: number; median_ms?: number; p90_ms?: number; llm_calls?: number; est_cost_usd?: number }
type SrcRow = { name: string; last_success?: string | null; circuit?: string }
type Status = { sources: SrcRow[]; meta?: { as_of?: string } }

async function getJson<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(String(r.status))
  return r.json() as Promise<T>
}
const link = (href: string, text: string) => (
  <a className="text-brand underline underline-offset-2" href={href} target="_blank" rel="noreferrer">{text}</a>
)

// Evidence for judges: static report numbers (public/evidence.json, hidden if missing) + live tiles (hidden on failure).
export default function JudgeEvidence() {
  const { t } = useApp()
  const [ev, setEv] = useState<{ generated_at?: string; items: Item[] } | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [status, setStatus] = useState<Status | null>(null)
  const [keys, setKeys] = useState<{ gemini?: boolean } | null>(null)
  const [liveFail, setLiveFail] = useState(false)
  useEffect(() => {
    getJson<{ generated_at?: string; items: Item[] }>('/evidence.json').then((j) => { if (Array.isArray(j.items) && j.items.length) setEv(j) }).catch(() => setEv(null))
    getJson<Stats>('/api/ai/stats?n=100').then(setStats).catch(() => setLiveFail(true))
    getJson<Status>('/api/status').then(setStatus).catch(() => setLiveFail(true))
    getJson<{ keys: { gemini?: boolean } }>('/api/health').then((h) => setKeys(h.keys)).catch(() => setLiveFail(true))
  }, [])
  const asOf = (d?: string) => t('p36.ev.asof').replace('{d}', d || '')
  const circuitOpen = status ? status.sources.filter((s) => s.circuit === 'open').length : 0
  const okCount = status ? status.sources.filter((s) => s.last_success).length : 0

  return (
    <Card title={t('p36.ev.h')}>
      <p className="mb-3 text-body-sm text-muted">{t('p36.ev.sub')}</p>
      {ev && (
        <ul className="space-y-3">
          {ev.items.map((i) => (
            <li key={i.id} className="rounded-lg border border-line p-3 text-body-sm">
              <p className="font-semibold text-ink">{i.label}: {i.value}</p>
              {i.detail && <p className="text-muted">{i.detail}</p>}
              <p className="mt-1 text-caption text-muted">
                {i.as_of && <>{asOf(i.as_of)} · </>}
                {i.source_url ? link(i.source_url, i.source_path || t('p36.ev.file')) : i.source_path && <code>{i.source_path}</code>}
              </p>
            </li>
          ))}
        </ul>
      )}
      {ev?.generated_at && <p className="mt-2 text-caption text-muted">{t('p36.ev.gen').replace('{d}', ev.generated_at)}</p>}
      <div className="mt-3 space-y-2">
        {stats && (
          <div className="rounded-lg border border-line p-3 text-body-sm">
            <p className="font-semibold text-ink">{t('p36.ai.h')}</p>
            {stats.n > 0 ? (
              <>
                <p className="text-muted">{t('p36.ai.body').replace('{n}', String(stats.n)).replace('{med}', String(Math.round(stats.median_ms ?? 0))).replace('{p90}', String(Math.round(stats.p90_ms ?? 0))).replace('{calls}', String(stats.llm_calls ?? 0))}</p>
                {typeof stats.est_cost_usd === 'number' && <p className="text-muted">{t('p36.ai.cost').replace('{c}', stats.est_cost_usd.toFixed(4))}</p>}
                <p className="mt-1 text-caption text-muted">{link('/api/ai/stats?n=100', '/api/ai/stats')}</p>
              </>
            ) : <p className="text-muted">{t('p36.ai.empty')}</p>}
          </div>
        )}
        {status && (
          <div className="rounded-lg border border-line p-3 text-body-sm">
            <p className="font-semibold text-ink">{t('p36.st.h')}</p>
            <p className="text-muted">{t('p36.st.body').replace('{ok}', String(okCount)).replace('{n}', String(status.sources.length)).replace('{open}', String(circuitOpen))}</p>
            <p className="mt-1 text-caption text-muted">{status.meta?.as_of && <>{asOf(status.meta.as_of)} · </>}<a className="text-brand underline underline-offset-2" href="#status">{t('p36.st.link')}</a></p>
          </div>
        )}
        {keys && (
          <p className="rounded-lg border border-line p-3 text-body-sm text-ink">{t(keys.gemini ? 'p36.hl.on' : 'p36.hl.off')}</p>
        )}
        {liveFail && !stats && !status && !keys && <p className="text-caption text-muted">{t('p36.ev.fail')}</p>}
      </div>
    </Card>
  )
}
