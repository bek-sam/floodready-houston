import { useEffect, useState } from 'react'
import { api } from '../../api'
import { useApp } from '../../ctx'
import { toProfile, usePlace, type Household } from '../../state/place'
import { Button, Sheet, toast } from '../ds'
import { HouseholdForm } from './HouseholdForm'

export function HouseholdSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t, lang } = useApp()
  const { household, setHousehold, place } = usePlace()
  const [draft, setDraft] = useState<Household>(household)
  useEffect(() => { if (open) setDraft(household) }, [open, household])
  const save = () => {
    setHousehold(draft)
    api.saveProfile(toProfile(draft, place, lang)).catch(() => { /* optional */ })
    toast(t('hh.saved'))
    onClose()
  }
  return (
    <Sheet open={open} onClose={onClose} title={t('hh.title')} footer={<Button full onClick={save}>{t('hh.saveBtn')}</Button>}>
      <p className="mb-4 text-body-sm text-muted">{t('hh.sub')}</p>
      <HouseholdForm value={draft} onChange={setDraft} />
    </Sheet>
  )
}
