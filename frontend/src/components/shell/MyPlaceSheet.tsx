import { useState } from 'react'
import { Eye, MapPin, Pencil, Users } from 'lucide-react'
import type { WatchPlace } from '../../api'
import { useApp } from '../../ctx'
import { householdChips, placeName, store, usePlace } from '../../state/place'
import { Button, Card, Sheet, toast } from '../ds'
import { PlaceForm } from './PlaceForm'

const loadWatched = (): WatchPlace[] => {
  const v = store.json<WatchPlace[]>('watchPlaces', [])
  return Array.isArray(v) ? v.filter((p) => p && typeof p.lat === 'number') : []
}

export function MyPlaceSheet({ open, onClose, onEditHousehold }: { open: boolean; onClose: () => void; onEditHousehold: () => void }) {
  const { t } = useApp()
  const { place, setPlace, household } = usePlace()
  const [editing, setEditing] = useState(false)
  const showForm = editing || !place
  const chips = householdChips(household)
  const watched = open ? loadWatched() : []
  const close = () => { setEditing(false); onClose() }

  return (
    <Sheet open={open} onClose={close} title={t('place.sheetTitle')}>
      <div className="space-y-6">
        {place && (
          <Card tone="inset" title={<span className="flex items-center gap-2"><MapPin aria-hidden size={18} className="text-brand" />{placeName(place.nickname, t)}</span>}
            action={!editing && <Button variant="ghost" size="sm" icon={Pencil} onClick={() => setEditing(true)}>{t('place.edit')}</Button>}>
            <p className="text-body-sm text-ink">{place.label}</p>
          </Card>
        )}
        {showForm && (
          <section aria-labelledby="mp-change">
            <h3 id="mp-change" className="mb-3 text-h3">{place ? t('place.changeAddress') : t('place.set')}</h3>
            <PlaceForm autoFocus onSaved={() => { setEditing(false); toast(t('place.saved')) }} />
            {editing && <Button variant="ghost" className="mt-2" full onClick={() => setEditing(false)}>{t('ds.cancel')}</Button>}
          </section>
        )}
        <section aria-labelledby="mp-hh">
          <h3 id="mp-hh" className="mb-2 flex items-center gap-2 text-h3"><Users aria-hidden size={18} className="text-brand" />{t('hh.title')}</h3>
          {chips.length ? (
            <ul className="mb-3 flex flex-wrap gap-2">
              {chips.map((k) => <li key={k} className="rounded-full bg-surface-2 px-3 py-1 text-caption text-ink">{t(k)}</li>)}
            </ul>
          ) : <p className="mb-3 text-body-sm text-muted">{t('hh.empty')}</p>}
          <Button variant="secondary" icon={Pencil} onClick={onEditHousehold}>{t('hh.edit')}</Button>
        </section>
        {watched.length > 0 && (
          <section aria-labelledby="mp-watch">
            <h3 id="mp-watch" className="mb-2 flex items-center gap-2 text-h3"><Eye aria-hidden size={18} className="text-brand" />{t('place.watched')}</h3>
            <ul className="divide-y divide-line rounded-md border border-line">
              {watched.map((w) => (
                <li key={w.id} className="flex items-center justify-between gap-2 p-3">
                  <span className="min-w-0 truncate text-body-sm">{w.label}</span>
                  <Button variant="ghost" size="sm" onClick={() => { setPlace({ lat: w.lat, lon: w.lon, label: w.label, nickname: w.label, zip: null, savedAt: '' }); toast(t('place.saved')) }}>
                    {t('place.makeMine')}
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </Sheet>
  )
}
