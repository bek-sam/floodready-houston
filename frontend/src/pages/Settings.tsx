import { useState } from 'react'
import { MapPin, Pencil, RotateCcw, Trash2, Users } from 'lucide-react'
import { useApp } from '../ctx'
import { householdChips, placeName, store, usePlace } from '../state/place'
import { Button, ButtonLink, Card, PageHeader, Segmented } from '../components/ds'
import { LanguageList } from '../components/shell/LanguageSheet'
import EasyReadToggle from '../components/easyread/EasyReadToggle'
import { useShell } from '../components/shell/ShellContext'

const DATA_KEYS = ['floodready.place.v1', 'floodready.household.v1', 'floodready.onboarded.v1', 'floodready.actionsDone.v1', 'watchPlaces', 'lastPlan', 'recoverDone']

export default function Settings() {
  const { t, lang, setLang, dark, setDark } = useApp()
  const { place, household } = usePlace()
  const { openPlaceSheet, openHouseholdSheet } = useShell()
  const [confirm, setConfirm] = useState(false)
  const chips = householdChips(household)
  const clear = () => {
    DATA_KEYS.forEach((k) => store.set(k, null))
    try { Object.keys(localStorage).filter((k) => k.startsWith('floodready.')).forEach((k) => localStorage.removeItem(k)) } catch { /* ignore */ }
    location.hash = '#home'
    location.reload()
  }
  return (
    <div className="space-y-6">
      <PageHeader title={t('nav.settings')} subtitle={t('settings.sub')} />
      <Card title={t('place.sheetTitle')}>
        {place ? (
          <p className="flex items-start gap-2 text-body-sm"><MapPin aria-hidden size={16} className="mt-0.5 shrink-0 text-brand" />
            <span><b>{placeName(place.nickname, t)}</b> · <bdi>{place.label}</bdi></span></p>
        ) : <p className="text-body-sm text-muted">{t('place.none')}</p>}
        <p className="mt-3 flex items-start gap-2 text-body-sm"><Users aria-hidden size={16} className="mt-0.5 shrink-0 text-brand" />
          <span>{chips.length ? chips.map((k) => t(k)).join(' · ') : t('hh.empty')}</span></p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="secondary" icon={MapPin} onClick={openPlaceSheet}>{place ? t('place.change') : t('place.set')}</Button>
          <Button variant="secondary" icon={Pencil} onClick={openHouseholdSheet}>{t('hh.edit')}</Button>
          <ButtonLink variant="ghost" icon={RotateCcw} href="#welcome">{t('settings.rerun')}</ButtonLink>
        </div>
      </Card>
      <Card title={t('language')}>
        <LanguageList value={lang} onChange={setLang} />
      </Card>
      <Card title={t('settings.appearance')}>
        <Segmented label={t('settings.appearance')} value={dark ? 'dark' : 'light'} onChange={(v) => setDark(v === 'dark')}
          options={[{ value: 'light', label: t('settings.light') }, { value: 'dark', label: t('settings.darkShort') }]} />
      </Card>
      <EasyReadToggle />
      <Card title={t('settings.data')} subtitle={t('settings.dataSub')}>
        {confirm ? (
          <div className="flex flex-wrap gap-2">
            <Button variant="danger" icon={Trash2} onClick={clear}>{t('settings.clearConfirm')}</Button>
            <Button variant="secondary" onClick={() => setConfirm(false)}>{t('ds.cancel')}</Button>
          </div>
        ) : <Button variant="secondary" icon={Trash2} onClick={() => setConfirm(true)}>{t('settings.clear')}</Button>}
      </Card>
    </div>
  )
}
