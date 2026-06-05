import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DccCompactStatus } from '../../lib/devDashboard/dccCompactStatus'
import { deployDriftTone } from '../../lib/devDashboard/dccCompactStatus'
import { toneClass } from '../../pages/devDashboardFilters'

export type DccCompactOverviewPanelProps = {
  compact: DccCompactStatus | null
  loading?: boolean
  rawDetailsJson?: string | null
}

export const DccCompactOverviewPanel: React.FC<DccCompactOverviewPanelProps> = ({
  compact,
  loading,
  rawDetailsJson,
}) => {
  const { t } = useTranslation()
  const driftTone = deployDriftTone(compact?.deploy_drift_status)
  const telemetryTone = compact?.telemetry?.health_ok ? 'green' : 'red'
  const dccTone = compact?.dcc_visible ? 'green' : 'yellow'

  const tiles = [
    {
      label: t('devDashboard.compact.profile', 'Profil'),
      value: compact?.install_profile ?? '—',
      tone: 'gray',
    },
    {
      label: t('devDashboard.compact.dcc', 'DCC'),
      value: compact?.dcc_visible ? 'sichtbar' : 'blockiert',
      tone: dccTone,
    },
    {
      label: t('devDashboard.compact.capability', 'Developer-Capability'),
      value: compact?.developer_capability?.valid
        ? 'gültig'
        : compact?.developer_capability?.configured
          ? 'Token fehlt/ungültig'
          : 'nicht konfiguriert',
      tone: compact?.developer_capability?.valid ? 'green' : 'yellow',
    },
    {
      label: t('devDashboard.compact.deployDrift', 'Deploy-Drift'),
      value: compact?.deploy_drift_status ?? '—',
      tone: driftTone,
    },
    {
      label: t('devDashboard.compact.telemetry', 'Telemetrie'),
      value: compact?.telemetry?.ingest_enabled ? 'ingest on' : 'ingest off',
      tone: telemetryTone,
    },
    {
      label: t('devDashboard.compact.rescueIso', 'Rescue-ISO'),
      value: compact?.rescue?.iso_uefi_validated ? 'UEFI ok' : 'pending',
      tone: compact?.rescue?.iso_uefi_validated ? 'green' : 'yellow',
    },
    {
      label: t('devDashboard.compact.usb', 'USB-Stick'),
      value: compact?.rescue?.usb_mount_detected
        ? 'eingehängt'
        : String(compact?.rescue?.usb_written ?? 'unknown'),
      tone: compact?.rescue?.usb_mount_detected ? 'green' : 'yellow',
    },
    {
      label: t('devDashboard.compact.targetBoot', 'MSI/W11 Boot'),
      value: compact?.rescue?.target_boot_validated ? 'bestätigt' : 'offen',
      tone: compact?.rescue?.target_boot_validated ? 'green' : 'red',
    },
  ]

  return (
    <section
      className="mb-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4"
      data-testid="dcc-compact-overview"
    >
      <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
        <div>
          <h2 className="text-sm font-semibold text-white">
            {t('devDashboard.compact.title', 'DCC Kompaktstatus')}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {t('devDashboard.compact.subtitle', 'Ampel + nächste Aktion — kein Voll-Dashboard-Rohdump.')}
          </p>
        </div>
        {loading ? <span className="text-xs text-slate-500">…</span> : null}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
        {tiles.map((tile) => (
          <div
            key={tile.label}
            className={`rounded-lg border px-3 py-2 ${toneClass(tile.tone)}`}
            data-testid={`dcc-compact-tile-${tile.label}`}
          >
            <div className="text-[10px] uppercase tracking-wide opacity-80">{tile.label}</div>
            <div className="font-semibold mt-1 font-mono">{tile.value}</div>
          </div>
        ))}
      </div>

      {compact?.blockers?.length ? (
        <div className="mt-3 rounded border border-red-800/40 bg-red-950/20 p-3 text-xs" data-testid="dcc-compact-blockers">
          <div className="font-semibold text-red-200">{t('devDashboard.compact.blockers', 'Blocker')}</div>
          <ul className="mt-1 list-disc pl-4 text-red-100/90 font-mono">
            {compact.blockers.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="mt-3 text-xs text-cyan-200/90 font-mono" data-testid="dcc-compact-next-action">
        {compact?.next_operator_action ?? t('devDashboard.compact.noAction', 'Keine Operator-Aktion hinterlegt.')}
      </p>

      {rawDetailsJson ? (
        <details className="mt-3" data-testid="dcc-compact-raw-details">
          <summary className="cursor-pointer text-[11px] text-slate-500">
            {t('devDashboard.compact.rawDetails', 'Roh-Details (optional, aufklappbar)')}
          </summary>
          <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-2 text-[10px] text-slate-400">
            {rawDetailsJson}
          </pre>
        </details>
      ) : null}
    </section>
  )
}
