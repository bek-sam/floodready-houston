import type { Status } from '../../api'
import { useApp } from '../../ctx'
import { gaugeLabelKey, gaugeLevel } from '../../lib/levels'
import { RiskBadge } from './RiskBadge'

/** Gauge category with a plain label ("Near flood stage"). Replaces StatusChip. */
export function StatusBadge({ status, size = 'sm' }: { status: Status | string | null | undefined; size?: 'sm' | 'md' }) {
  const { t } = useApp()
  return <RiskBadge level={gaugeLevel(status)} label={t(gaugeLabelKey(status))} size={size} />
}
