import { useState } from 'react'
import { useApp } from '../../ctx'
import { store } from '../../state/place'
import { Card, Checkbox, SourceLink } from '../ds'

const KEY = 'floodready.pets.v1'
const ITEMS = ['id', 'photo', 'carrier', 'food', 'meds', 'leash', 'comfort', 'plan', 'never'] as const

/** Sourced pet checklist (Ready.gov/pets). No invented shelters or phone numbers. */
export default function PetsCard() {
  const { t } = useApp()
  const [done, setDone] = useState<Record<string, boolean>>(() => store.json(KEY, {}))
  const toggle = (id: string, v: boolean) => { const n = { ...done, [id]: v }; setDone(n); store.set(KEY, JSON.stringify(n)) }
  return (
    <Card id="prepare-pets" title={t('pets.h')} titleAs="h2" subtitle={t('pets.sub')}>
      <ul className="space-y-1">
        {ITEMS.map((i) => (
          <li key={i}><Checkbox checked={!!done[i]} onChange={(v) => toggle(i, v)}
            label={<span className={done[i] ? 'text-muted line-through' : ''}>{t('pets.i.' + i)}</span>} /></li>
        ))}
      </ul>
      <p className="mt-3 rounded-md border border-line bg-surface px-3 py-2 text-body-sm font-semibold text-ink">{t('pets.shelter')}</p>
      <p className="mt-2 text-caption text-muted">{t('pets.livestock')}</p>
      <p className="mt-2 flex flex-wrap items-center gap-2 text-caption text-muted">{t('pets.src')} <SourceLink href="https://www.ready.gov/pets" /></p>
    </Card>
  )
}
