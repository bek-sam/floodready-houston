import { BookOpenText } from 'lucide-react'
import { useApp } from '../../ctx'
import { Card, Segmented } from '../ds'
import { useEasy } from './easyRead'

export default function EasyReadToggle() {
  const { t } = useApp()
  const [on, set] = useEasy()
  return (
    <Card title={t('p11a.easy.title')} subtitle={t('p11a.easy.sub')}>
      <p className="mb-3 flex items-start gap-2 text-body-sm"><BookOpenText aria-hidden size={16} className="mt-0.5 shrink-0 text-brand" />{t('p11a.easy.what')}</p>
      <Segmented label={t('p11a.easy.title')} value={on ? 'on' : 'off'} onChange={(v) => set(v === 'on')}
        options={[{ value: 'off', label: t('p11a.easy.off') }, { value: 'on', label: t('p11a.easy.on') }]} />
    </Card>
  )
}
