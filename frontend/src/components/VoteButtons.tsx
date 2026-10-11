import { useState } from 'react'
import { api, errText } from '../api'
import { useApp } from '../ctx'
import { Button, toast } from './ds'

const KEY = 'fr.reportVotes'
const read = (): Record<string, boolean> => { try { return JSON.parse(localStorage.getItem(KEY) || '{}') } catch { return {} } }
const mark = (id: string) => { try { localStorage.setItem(KEY, JSON.stringify({ ...read(), [id]: true })) } catch { /* ignore */ } }

/** "Still there" / "Cleared" votes on a community report. Counts default to 0 when absent. */
export default function VoteButtons({ id, confirms, clears, lastVoteAt }: { id?: string; confirms?: number | null; clears?: number | null; lastVoteAt?: string | null }) {
  const { t } = useApp()
  const [c, setC] = useState({ y: confirms ?? 0, n: clears ?? 0, at: lastVoteAt ?? null })
  const [done, setDone] = useState(() => (id ? !!read()[id] : false))
  const [busy, setBusy] = useState(false)
  if (!id) return null
  const cleared = c.n >= 2 && c.n > c.y
  const vote = async (still: boolean) => {
    if (done || busy) return
    setBusy(true)
    try {
      const r = await api.voteReport(id, still)
      setC({ y: r.confirms ?? 0, n: r.clears ?? 0, at: r.last_vote_at ?? null }); mark(id); setDone(true); toast(t('p32.vote.thanks'))
    } catch (e) { toast({ message: errText(e, t('offline')), tone: 'error' }) } finally { setBusy(false) }
  }
  const ago = c.at && !isNaN(Date.parse(c.at)) ? Math.max(0, Math.round((Date.now() - Date.parse(c.at)) / 60000)) : null
  return (
    <div className="mt-1">
      <div className="flex flex-wrap items-center gap-1">
        <Button variant="secondary" size="sm" disabled={done || busy} onClick={() => vote(true)}>{t('p32.vote.still')}</Button>
        <Button variant="secondary" size="sm" disabled={done || busy} onClick={() => vote(false)}>{t('p32.vote.cleared')}</Button>
        {cleared && <span className="rounded-sm border border-dashed border-ui px-1.5 text-caption font-medium text-muted">{t('p32.vote.clearedTag')}</span>}
      </div>
      <p className="text-caption text-muted" role="status">
        {t('p32.vote.counts').replace('{y}', String(c.y)).replace('{n}', String(c.n))}
        {ago != null && ` · ${t('p32.vote.last').replace('{m}', String(ago))}`} · {t('p32.vote.note')}
      </p>
    </div>
  )
}
