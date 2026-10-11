import { useEffect, useState } from 'react'
import { Printer } from 'lucide-react'
import { apiC20, type Evac } from '../../api'
import { useApp } from '../../ctx'
import { store, usePlace } from '../../state/place'
import { Button, Card, Checkbox, Field, Input, SourceLink } from '../ds'
import { zoneState } from '../evac/EvacSurgeCard'
import { bagItems } from './items'

const DONE_KEY = 'floodready.gobag.v1'
const CARD_KEY = 'floodready.walletcard.v1'
interface CardData { name: string; contacts: string; meds: string }
const GROUPS = ['docs', 'health', 'family', 'basics', 'plan'] as const

const PRINT_CSS = `@media print{body *{visibility:hidden!important}.fr-print,.fr-print *{visibility:visible!important}
.fr-print{position:absolute;left:0;top:0;width:100%;padding:12px}.fr-noprint{display:none!important}
.fr-wallet{break-inside:avoid;border:1px solid #000!important;color:#000!important;background:#fff!important}}`

export default function GoBag() {
  const { t } = useApp()
  const { place, household: h } = usePlace()
  const items = bagItems(h)
  const [done, setDone] = useState<Record<string, boolean>>(() => store.json(DONE_KEY, {}))
  const [card, setCard] = useState<CardData>(() => {
    const c = store.json<Partial<CardData>>(CARD_KEY, {})
    return { name: c.name ?? '', contacts: c.contacts ?? '', meds: c.meds ?? h.medical.other }
  })
  const [evac, setEvac] = useState<Evac | null>(null)
  useEffect(() => {
    if (!place) { setEvac(null); return }
    let live = true
    apiC20.evac(place).then((e) => { if (live) setEvac(e) })
    return () => { live = false }
  }, [place?.lat, place?.lon]) // eslint-disable-line react-hooks/exhaustive-deps
  const toggle = (id: string, v: boolean) => { const n = { ...done, [id]: v }; setDone(n); store.set(DONE_KEY, JSON.stringify(n)) }
  const edit = (k: keyof CardData, v: string) => { const n = { ...card, [k]: v }; setCard(n); store.set(CARD_KEY, JSON.stringify(n)) }
  const doneN = items.filter((i) => done[i.id]).length
  const zs = evac ? zoneState(evac) : null
  const zone = !evac ? t('p10.zoneUnknown') : zs === 'unavailable' ? t('p10.zoneUnavail') : zs === 'in' ? evac.zone_label || `${t('p10.zone')} ${evac.zone ?? ''}` : t('p10.noZone')

  return (
    <div className="space-y-4">
      <style>{PRINT_CSS}</style>
      <Card id="prepare-gobag" title={t('p10.bag.h')} titleAs="h2" subtitle={t('p10.bag.sub')}
        action={<Button variant="secondary" icon={Printer} className="fr-noprint" onClick={() => window.print()}>{t('p10.print')}</Button>}>
        <div className="fr-print space-y-4">
          <p className="text-body-sm text-muted" role="status">{t('p10.bag.progress').replace('{n}', String(doneN)).replace('{m}', String(items.length))}</p>
          {GROUPS.map((g) => {
            const list = items.filter((i) => i.group === g)
            return list.length ? (
              <div key={g}>
                <h3 className="mb-1 text-h3 text-ink">{t('p10.grp.' + g)}</h3>
                <ul className="space-y-1">
                  {list.map((i) => (
                    <li key={i.id}><Checkbox checked={!!done[i.id]} onChange={(v) => toggle(i.id, v)}
                      label={<span className={done[i.id] ? 'text-muted line-through' : ''}>{t(i.key)}</span>} /></li>
                  ))}
                </ul>
              </div>
            ) : null
          })}
          <p className="text-caption text-muted">{t('p10.bag.sources')}{' '}
            <SourceLink href="https://www.ready.gov/kit" label="Ready.gov" /> · <SourceLink href="https://www.ready.gov/disability" label="Ready.gov" /> · <SourceLink href="https://www.cdc.gov/kidney-disease/caring/" label="CDC" /></p>
          <div className="grid gap-3 sm:grid-cols-2">
            <section className="fr-wallet rounded-lg border border-line bg-surface p-3 text-body-sm text-ink" aria-label={t('p10.card.front')}>
              <p className="text-caption font-semibold uppercase text-muted">{t('p10.card.front')}</p>
              <p className="text-h3">{card.name || t('p10.card.nameBlank')}</p>
              <p><bdi>{place?.label ?? ''}</bdi></p>
              <p className="mt-1"><b>{t('p10.card.contacts')}:</b> {card.contacts || '________'}</p>
              <p><b>{t('p10.card.meds')}:</b> {card.meds || '________'}</p>
              <p className="mt-1 font-semibold">{t('p10.card.stear')}</p>
            </section>
            <section className="fr-wallet rounded-lg border border-line bg-surface p-3 text-body-sm text-ink" aria-label={t('p10.card.back')}>
              <p className="text-caption font-semibold uppercase text-muted">{t('p10.card.back')}</p>
              <p className="text-h3">{t('p10.card.zone')}: {zone}</p>
              <p className="mt-1 text-caption">{t('p10.card.note')}</p>
            </section>
          </div>
        </div>
      </Card>
      <Card title={t('p10.card.edit')} titleAs="h2" className="fr-noprint">
        <div className="space-y-3">
          <Field label={t('p10.card.name')}><Input value={card.name} onChange={(e) => edit('name', e.target.value)} autoComplete="name" /></Field>
          <Field label={t('p10.card.contacts')}><Input value={card.contacts} onChange={(e) => edit('contacts', e.target.value)} placeholder={t('p10.card.contactsPh')} /></Field>
          <Field label={t('p10.card.meds')}><Input value={card.meds} onChange={(e) => edit('meds', e.target.value)} /></Field>
          <p className="text-caption text-muted">{t('p10.local')}</p>
        </div>
      </Card>
    </div>
  )
}
