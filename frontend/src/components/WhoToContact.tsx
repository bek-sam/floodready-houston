import { useState } from 'react'
import { Copy, Globe, Mail, Phone } from 'lucide-react'
import type { Civic, Official } from '../api'
import { useApp } from '../ctx'
import { Button, ButtonLink, Card } from './ds'

const ROLES = ['commissioner', 'council', 'floodplain_admin'] as const
const safeUrl = (u?: string) => (typeof u === 'string' && u && /^https?:\/\//i.test(u) ? u : undefined)

export default function WhoToContact({ civic }: { civic: Civic }) {
  const { t } = useApp()
  const [copied, setCopied] = useState(false)
  const [err, setErr] = useState(false)
  const off = civic.officials
  const hasName = (o: Official) => !!(o.name ?? o.title ?? o.office)
  const hasContact = (o: Official) => !!(o.phone || o.email || safeUrl(o.url))
  const list = off ? ROLES.map((r) => [r, off[r]] as const).filter((x): x is [typeof ROLES[number], Official] => !!x[1] && typeof x[1] === 'object' && (hasName(x[1]) || (x[0] === 'council' && !!x[1].district) || hasContact(x[1]))) : []
  const proj = civic.bond?.projects?.[0]?.name
  const msg = proj ? t('c11.who.msgProject').replace('{project}', proj) : t('c11.who.msgGeneric')
  const copy = async () => {
    setErr(false)
    try { await navigator.clipboard.writeText(msg); setCopied(true) } catch { setErr(true) }
  }
  if (list.length === 0) return <Card title={t('c11.who.title')}><p className="text-body-sm text-muted">{t('c11.who.empty')}</p></Card>
  return (
    <Card title={t('c11.who.title')} subtitle={t('c11.who.intro')}>
      <ul className="divide-y divide-line">
        {list.map(([role, o]) => (
          <li key={role} className="py-3 first:pt-0">
            <p className="text-overline uppercase text-muted">{t('c11.who.' + role)}</p>
            <p className="text-base font-semibold text-ink">{hasName(o) ? (o.name ?? o.title ?? o.office) : role === 'council' && o.district ? t('p29.who.district').replace('{d}', String(o.district)) : t('p29.who.office')}{hasName(o) && o.district ? ` · ${o.district}` : ''}{o.precinct != null && o.precinct !== '' ? ` · ${t('c11.who.precinct')} ${o.precinct}` : ''}</p>
            {o.entity && <p className="text-caption text-muted">{o.entity}</p>}
            <div className="mt-2 flex flex-wrap gap-2">
              {typeof o.phone === 'string' && o.phone && <ButtonLink variant="secondary" size="sm" icon={Phone} href={'tel:' + o.phone.replace(/[^\d+]/g, '')}>{t('c11.who.call')} {o.phone}</ButtonLink>}
              {typeof o.email === 'string' && o.email && <ButtonLink variant="secondary" size="sm" icon={Mail} href={'mailto:' + o.email}>{t('c11.who.email')}</ButtonLink>}
              {safeUrl(o.url) && <ButtonLink variant="secondary" size="sm" icon={Globe} href={safeUrl(o.url)} target="_blank" rel="noreferrer">{t('c11.who.web')}</ButtonLink>}
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-body-sm font-semibold text-ink">{t('c11.who.msgTitle')}</p>
      <p className="mt-1 rounded-md bg-surface-2 p-3 text-body-sm text-ink">{msg}</p>
      <Button variant="secondary" icon={Copy} className="mt-2" onClick={copy}>{copied ? t('c11.who.copied') : t('c11.who.copy')}</Button>
      {err && <p className="mt-1 text-body-sm text-danger" role="alert">{t('c11.who.copyFail')}</p>}
    </Card>
  )
}
