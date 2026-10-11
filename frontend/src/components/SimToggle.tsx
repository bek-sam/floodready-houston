import { DemoPanel, Switch } from './ds'
import { useApp } from '../ctx'
import { useSimStorm } from '../state/place'

/** The one demo-storm switch (Home, Alerts, Drive). Renders nothing outside demo mode. */
export default function SimToggle({ className = '' }: { className?: string }) {
  const { t } = useApp()
  const { sim, setSim, demo } = useSimStorm()
  if (!demo) return null
  return (
    <DemoPanel className={className}>
      <Switch label={t('p34.toggle')} description={t('p34.toggleHint')} checked={sim} onChange={setSim} />
    </DemoPanel>
  )
}
