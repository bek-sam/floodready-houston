import { Phone, Printer } from 'lucide-react'
import { useApp } from '../ctx'
import StayInformed from '../components/p38/StayInformed'
import { Button, Card, PageHeader, SourceLink } from '../components/ds'
import { FAMILY_KEY, type Contact } from '../components/share/planShare'
import { fmtAt, EVAC_CACHE, HOME_CACHE } from '../lib/offline'
import { householdChips, store, usePlace } from '../state/place'
import type { Risk } from '../api'

const PRINT_CSS = `@media print{body *{visibility:hidden!important}.fr-print,.fr-print *{visibility:visible!important}
.fr-print{position:absolute;left:0;top:0;width:100%;padding:12px}.fr-noprint{display:none!important}}`
const SRC = [
  { href: 'https://www.ready.gov/communicate', label: 'Ready.gov Make a Plan' },
  { href: 'https://www.ready.gov/kit', label: 'Ready.gov Emergency Kit' },
  { href: 'https://www.ready.gov/power-outages', label: 'Ready.gov Power Outages' },
]

/** One-screen safety card built only from localStorage. Works with no signal. */
export default function Offline() {
  const { t, lang } = useApp()
  const { household } = usePlace()
  const home = store.json<Record<string, { at: number; data: unknown }>>(HOME_CACHE, {})
  const risk = home.risk?.data as Risk | undefined
  const evac = store.json<{ at: number; zone: string | null } | null>(EVAC_CACHE, null)
  const fam = store.json<{ meeting?: string; contacts?: Contact[] }>(FAMILY_KEY, {})
  const contacts = (Array.isArray(fam.contacts) ? fam.contacts : []).filter((c) => c && (c.name || c.phone))
  const chips = householdChips(household)
  const line = (k: string, v: Record<string, string>) => Object.entries(v).reduce((s, [a, b]) => s.replace(`{${a}}`, b), t(k))
  const nums = [['911', 'p37.card.n911'], ['311', 'p37.card.n311'], ['211', 'p37.card.n211']]

  return (
    <div className="space-y-4">
      <style>{PRINT_CSS}</style>
      <PageHeader title={t('p37.card.title')} />
      <p className="text-body-sm text-muted">{t('p37.card.intro')}</p>
      <Button variant="secondary" icon={Printer} className="fr-noprint" onClick={() => window.print()}>{t('p37.card.print')}</Button>
      <div className="fr-print space-y-4">
        <Card title={t('p37.card.nums')} titleAs="h2">
          <ul className="space-y-2">
            {nums.map(([n, k]) => (
              <li key={n}><a href={`tel:${n}`} className="flex min-h-11 items-center gap-3 rounded-md border border-ui bg-surface px-3 py-2 text-ink">
                <Phone aria-hidden size={18} className="shrink-0" /><b className="w-10 shrink-0 text-h3">{n}</b><span className="text-body-sm">{t(k)}</span></a></li>
            ))}
          </ul>
        </Card>
        <Card title={t('p37.card.rules')} titleAs="h2">
          <ul className="list-disc space-y-1 ps-5 text-body">
            {['r1', 'r2', 'r3'].map((r) => <li key={r}>{t('p37.card.' + r)}</li>)}
          </ul>
        </Card>
        <Card title={t('p37.card.risk')} titleAs="h2">
          {risk ? (
            <ul className="space-y-1 text-body">
              {risk.fema_zone && <li>{line('p37.card.zone', { z: risk.fema_zone })}</li>}
              {risk.elevation_ft != null && <li>{line('p37.card.elev', { e: String(Math.round(risk.elevation_ft)) })}</li>}
              {evac?.zone && <li>{line('p37.card.evac', { z: evac.zone })}</li>}
              <li className="text-caption text-muted">{line('p37.card.saved', { time: fmtAt(home.risk.at, lang) })}</li>
            </ul>
          ) : <p className="text-body-sm text-muted">{t('p37.card.riskNone')}</p>}
        </Card>
        <Card title={t('p37.card.hh')} titleAs="h2">
          {chips.length ? <ul className="flex flex-wrap gap-2">{chips.map((k) => <li key={k} className="rounded-full bg-surface-2 px-3 py-1 text-body-sm text-ink">{t(k)}</li>)}</ul>
            : <p className="text-body-sm text-muted">{t('p37.card.hhNone')}</p>}
        </Card>
        <Card title={t('p37.card.meet')} titleAs="h2">
          {fam.meeting || contacts.length ? (
            <div className="space-y-2 text-body">
              {fam.meeting && <p>{fam.meeting}</p>}
              <ul className="space-y-1">{contacts.map((c, i) => (
                <li key={i}>{c.name} {c.phone && <a href={`tel:${c.phone}`} className="font-semibold text-brand underline">{c.phone}</a>}</li>))}</ul>
            </div>
          ) : <p className="text-body-sm text-muted">{t('p37.card.meetNone')}</p>}
        </Card>
        <p className="text-body-sm text-ink">{t('p37.card.kit')}</p>
        <p className="text-caption text-muted">{t('p37.card.src')}: {SRC.map((s) => <SourceLink key={s.href} href={s.href} label={s.label} />)}</p>
      </div>
      <div className="fr-noprint"><StayInformed /></div>
    </div>
  )
}
