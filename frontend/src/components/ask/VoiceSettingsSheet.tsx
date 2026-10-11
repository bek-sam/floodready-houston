import { useApp } from '../../ctx'
import { useDemoMode } from '../../state/place'
import { Button, Segmented, Sheet, Switch, type SegOption } from '../ds'

export type Engine = 'fast' | 'live' | 'el'

/** Voice settings: plain-language engine names ("Standard" default). The ElevenLabs agent shows in demo mode only. */
export function VoiceSettingsSheet({ open, onClose, engine, onEngine, aloud, onAloud }: {
  open: boolean; onClose: () => void; engine: Engine; onEngine: (e: Engine) => void; aloud: boolean; onAloud: (v: boolean) => void
}) {
  const { t } = useApp()
  const { demo } = useDemoMode()
  const options: SegOption<Engine>[] = [
    { value: 'fast', label: t('p4.set.standard') },
    { value: 'live', label: t('p4.set.live') },
    ...(demo ? [{ value: 'el' as const, label: t('p4.set.el') }] : []),
  ]
  return (
    <Sheet open={open} onClose={onClose} title={t('p4.set.title')} footer={<Button full onClick={onClose}>{t('p4.set.done')}</Button>}>
      <div className="space-y-4">
        <div>
          <p className="mb-2 text-body-sm font-medium text-ink">{t('p4.set.voice')}</p>
          <Segmented options={options} value={engine} onChange={onEngine} label={t('p4.set.voice')} />
          <p className="mt-2 text-body-sm text-muted">{t(engine === 'fast' ? 'p4.set.standard.d' : engine === 'live' ? 'p4.set.live.d' : 'p4.set.el.d')}</p>
        </div>
        <Switch label={t('p4.set.aloud')} checked={aloud} onChange={onAloud} />
      </div>
    </Sheet>
  )
}
