import React from 'react'
import { useTranslation } from 'react-i18next'
import {
  buildPortLabels,
  capabilitySummaryLabel,
  dccVisibilityLabel,
  formatAckLabel,
  formatIngestLabel,
  formatTelemetryHealthLabel,
  type DccLiveStatusSnapshot,
} from '../../lib/devDashboard/dccLiveStatus'
import type { DccGateVersionInfo } from '../../lib/devDashboard/dccGate'

export type DccCompactStatusBarProps = {
  live: DccLiveStatusSnapshot | null
  statusHttp: number
  versionPayload: DccGateVersionInfo | null
}

export const DccCompactStatusBar: React.FC<DccCompactStatusBarProps> = ({
  live,
  statusHttp,
  versionPayload,
}) => {
  const { t } = useTranslation()
  const cap = live?.capability ?? null
  const telemetry = live?.telemetry ?? null
  const ports = buildPortLabels(versionPayload)
  const profile = cap?.install_profile ?? versionPayload?.install_profile ?? 'unknown'

  const items = [
    {
      label: t('devDashboard.liveStatus.dcc', 'DCC'),
      value: dccVisibilityLabel(cap, statusHttp),
    },
    {
      label: t('devDashboard.liveStatus.profile', 'Profil'),
      value: profile,
    },
    {
      label: t('devDashboard.liveStatus.capability', 'Developer-Capability'),
      value: capabilitySummaryLabel(cap),
    },
    {
      label: t('devDashboard.liveStatus.telemetryHealth', 'Telemetrie-Health'),
      value: formatTelemetryHealthLabel(live?.telemetryHttp ?? 0, telemetry),
    },
    {
      label: t('devDashboard.liveStatus.ingest', 'Ingest'),
      value: formatIngestLabel(telemetry),
    },
    { label: t('devDashboard.liveStatus.api', 'API'), value: ports.api },
    { label: t('devDashboard.liveStatus.ui', 'UI'), value: ports.ui },
    {
      label: t('devDashboard.liveStatus.lastAck', 'Letzter ACK'),
      value: formatAckLabel(telemetry),
    },
  ]

  return (
    <div
      className="mb-4 rounded-lg border border-slate-700/80 bg-slate-900/60 px-3 py-2"
      data-testid="dcc-compact-status-bar"
    >
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] font-mono text-slate-300">
        {items.map((item) => (
          <span key={item.label} data-testid={`dcc-live-${item.label}`}>
            <span className="text-slate-500">{item.label}:</span> {item.value}
          </span>
        ))}
        {cap?.reason ? (
          <span className="text-slate-500" data-testid="dcc-live-reason">
            reason={cap.reason}
          </span>
        ) : null}
        {telemetry?.last_error_code ? (
          <span className="text-amber-400/90" data-testid="dcc-live-last-error">
            last_error={telemetry.last_error_code}
          </span>
        ) : null}
      </div>
    </div>
  )
}
