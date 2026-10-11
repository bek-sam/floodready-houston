import { useState } from 'react'
import { Copy, Share2, TriangleAlert } from 'lucide-react'
import { useApp } from '../../ctx'
import { store, usePlace } from '../../state/place'
import { Button, Card, Checkbox, Field, Input, toast } from '../ds'
import { encodePlan, FAMILY_KEY, type Contact } from './planShare'


/** Builds a #share= link from the household plan, meeting place and contacts. Nothing is sent to a server. */
export default function SharePlanCard() {
  const { t } = useApp()
  const { household } = usePlace()
  const saved = store.json<{ meeting?: string; contacts?: Contact[] }>(FAMILY_KEY, {})
  const [meeting, setMeeting] = useState(typeof saved.meeting === 'string' ? saved.meeting : '')
  const [contacts, setContacts] = useState<Contact[]>(() => { const c = Array.isArray(saved.contacts) ? saved.contacts : []; return [0, 1].map((i) => ({ name: String(c[i]?.name ?? ''), phone: String(c[i]?.phone ?? '') })) })
  const [phones, setPhones] = useState(false)
  const [link, setLink] = useState<string | null>(null)
  const [big, setBig] = useState(false)
  const set = (i: number, k: keyof Contact, v: string) => setContacts((c) => c.map((x, j) => (j === i ? { ...x, [k]: v } : x)))

  function make() {
    store.set(FAMILY_KEY, JSON.stringify({ meeting, contacts }))
    const frag = encodePlan({ household, meeting, contacts: contacts.filter((c) => c.name.trim() || c.phone.trim()) }, phones)
    setBig(!frag); setLink(frag ? location.origin + location.pathname + frag : null)
  }
  async function copy() {
    if (!link) return
    try { await navigator.clipboard.writeText(link); toast(t('p15.share.copied')) } catch { /* user can select the text */ }
  }
  return (
    <Card title={<span className="flex items-center gap-2"><Share2 aria-hidden size={18} className="text-brand" />{t('p15.share.btn')}</span>} titleAs="h2" subtitle={t('p15.share.sub')}>
      <div className="space-y-3">
        <Field label={t('p15.share.meet')}><Input value={meeting} maxLength={160} onChange={(e) => setMeeting(e.target.value)} /></Field>
        {[0, 1].map((i) => (
          <div key={i} className="grid gap-3 sm:grid-cols-2">
            <Field label={t(i ? 'p15.share.c2' : 'p15.share.c1')}><Input value={contacts[i].name} maxLength={60} onChange={(e) => set(i, 'name', e.target.value)} /></Field>
            <Field label={t(i ? 'p15.share.p2' : 'p15.share.p1')}><Input type="tel" value={contacts[i].phone} maxLength={20} onChange={(e) => set(i, 'phone', e.target.value)} /></Field>
          </div>
        ))}
        <Checkbox label={t('p15.share.incPhone')} checked={phones} onChange={setPhones} />
        <div className="flex items-start gap-2 rounded-md bg-surface-2 p-3" role="note">
          <TriangleAlert aria-hidden size={18} className="mt-0.5 shrink-0 text-watch" />
          <p className="text-body-sm text-ink">{t('p15.share.warn')}</p>
        </div>
        <Button onClick={make}>{t('p15.share.make')}</Button>
        {big && <p role="alert" className="text-body-sm text-danger">{t('p15.share.big')}</p>}
        {link && (
          <div className="space-y-2">
            <textarea readOnly value={link} rows={3} aria-label={t('p15.share.copy')} onFocus={(e) => e.currentTarget.select()}
              className="w-full break-all rounded-sm border border-ui bg-surface p-2 text-caption text-ink" />
            <Button variant="secondary" icon={Copy} onClick={copy}>{t('p15.share.copy')}</Button>
          </div>
        )}
      </div>
    </Card>
  )
}
