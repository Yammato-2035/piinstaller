import type { CockpitPanelProps } from './types'
import { StatusCard } from './StatusCard'

export function ReleaseGatePanel({ dashboard, t }: CockpitPanelProps) {
  const gates = (dashboard?.br001_gates as Record<string, unknown>) || {}
  const offline = (gates.offline as Record<string, unknown>) || {}
  const live = (gates.live as Record<string, unknown>) || {}
  const offlineStatus = String(offline.status || dashboard?.release_gate_br001_offline_status || dashboard?.release_gate_status || 'gray')
  const liveStatus = String(live.status || 'red')
  const primary = String(gates.primary_release_gate || 'BR-001-OFFLINE')

  return (
    <div className="space-y-2" data-testid="dev-dashboard-release-gate-panel">
      <StatusCard
        label={t('devDashboard.releaseGateOffline', { id: primary })}
        value={offlineStatus}
        tone={offlineStatus}
        testId="dev-dashboard-release-gate-offline"
      />
      <StatusCard
        label={t('devDashboard.releaseGateLive')}
        value={`${liveStatus} · ${t('devDashboard.rescueStickBoard.experimental')}`}
        tone={liveStatus}
        testId="dev-dashboard-release-gate-live"
      />
      <p className="text-[10px] text-slate-500 break-all">{String(dashboard?.release_gate_path ?? '')}</p>
    </div>
  )
}
