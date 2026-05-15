import type { CockpitPanelProps } from './types'
import { StatusCard } from './StatusCard'

export function ReleaseGatePanel({ dashboard, t }: CockpitPanelProps) {
  return (
    <StatusCard
      label={t('devDashboard.releaseGate')}
      value={String(dashboard?.release_gate_status ?? t('devDashboard.noData'))}
      tone={String(dashboard?.release_gate_status || 'gray')}
      testId="dev-dashboard-release-gate-card"
    />
  )
}
