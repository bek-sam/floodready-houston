import { useState } from 'react'
import { useApp } from '../../ctx'
import { householdChips, KEYS, store } from '../../state/place'
import { Button, ButtonLink, Card } from '../ds'
import { decodePlan, FAMILY_KEY } from './planShare'

/** Read-only view of a #share= plan. Saving writes to this device only. */
export default function SharedPlan() {
  const { t } = useApp()
  const [plan] = useState(() => decodePlan(location.hash))
  const [saved, setSaved] = useState(false)
  const save = () => {
    if (!plan) return
    store.set(KEYS.household, JSON.stringify(plan.household))
    store.set(FAMILY_KEY, JSON.stringify({ meeting: plan.meeting, contacts: plan.contacts }))
    setSaved(true)
  }
  return (
    <main className="mx-auto max-w-[640px] space-y-4 px-4 py-6">
      <h1 className="text-h1 text-ink">{t('p15.view.title')}</h1>
      {!plan ? <Card tone="watch"><p role="alert" className="text-body">{t('p15.view.invalid')}</p></Card> : (
        <>
          <p className="text-body-sm text-muted">{t('p15.view.sub')}</p>
          <Card title={t('p15.view.household')} titleAs="h2">
            {householdChips(plan.household).length
              ? <ul className="flex flex-wrap gap-2">{householdChips(plan.household).map((k) => <li key={k} className="rounded-full bg-surface-2 px-3 py-1 text-body-sm text-ink">{t(k)}</li>)}</ul>
              : <p className="text-body-sm text-muted">{t('p15.view.none')}</p>}
          </Card>
          <Card title={t('p15.view.meet')} titleAs="h2"><p className="text-body text-ink">{plan.meeting || t('p15.view.none')}</p></Card>
          <Card title={t('p15.view.contacts')} titleAs="h2">
            {plan.contacts.length ? <ul className="space-y-1">{plan.contacts.map((c, i) => <li key={i} className="text-body text-ink">{c.name}{c.phone ? ` · ${c.phone}` : ''}</li>)}</ul> : <p className="text-body-sm text-muted">{t('p15.view.none')}</p>}
          </Card>
          <p className="text-caption text-muted">{t('p15.view.replace')}</p>
          {saved ? <p role="status" className="text-body font-semibold text-ink">{t('p15.view.saved')}</p> : <Button size="lg" onClick={save}>{t('p15.view.save')}</Button>}
        </>
      )}
      <ButtonLink variant="secondary" href={location.pathname + '#home'} onClick={() => setTimeout(() => location.reload(), 0)}>{t('p15.view.open')}</ButtonLink>
    </main>
  )
}
