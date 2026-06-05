import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { buildCardViewModel, buildCardViewModelFromSample, type WindowsRescueCardViewModel } from '../../lib/devDashboard/windowsRescueInspectReport'

export type WindowsRescueInspectCardProps = {
  viewModel?: WindowsRescueCardViewModel
  useSampleReport?: boolean
  planningOnly?: boolean
}

export const WindowsRescueInspectCard: React.FC<WindowsRescueInspectCardProps> = ({
  viewModel,
  useSampleReport = true,
  planningOnly = true,
}) => {
  const { t } = useTranslation()
  const vm = useMemo(() => {
    if (viewModel) return viewModel
    if (useSampleReport) return buildCardViewModelFromSample()
    return buildCardViewModel(null)
  }, [viewModel, useSampleReport])

  if (!vm.report && !useSampleReport) {
    return (
      <section className="rounded-xl border border-amber-800/40 bg-amber-950/10 p-4" data-testid="windows-rescue-inspect-card">
        <p className="text-xs text-amber-200">{t('devDashboard.windowsRescue.noReport', 'no_windows_inspect_report_available')}</p>
      </section>
    )
  }

  return (
    <section
      className="rounded-xl border border-cyan-800/40 bg-cyan-950/15 p-4"
      data-testid="windows-rescue-inspect-card"
    >
      <h2 className="text-sm font-semibold text-white">
        {t('devDashboard.windowsRescue.title', 'Windows Rescue Inspect')}
      </h2>
      {planningOnly ? (
        <p className="text-xs text-slate-400 mt-1">
          {t('devDashboard.windowsRescue.sampleReport', 'Operator-Readonly-Sample — kein HW-Lauf')}
        </p>
      ) : null}

      <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3 text-xs">
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-bitlocker">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.bitlocker', 'BitLocker')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {vm.report?.bitlocker?.status ?? 'unknown'}</li>
            <li>access: {String(vm.report?.bitlocker?.access_allowed ?? false)}</li>
            <li>volume: {vm.bitlocker.volume_lock_status}</li>
            <li>block: {vm.report?.bitlocker?.blocking_reason ?? '—'}</li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-telemetry">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.telemetry', 'Telemetrie')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {vm.telemetry.telemetry_status}</li>
            <li>queue: {vm.telemetry.queue_depth ?? 0}</li>
            <li>ack_id: {vm.telemetry.server_ack_id ?? '—'}</li>
            <li>
              hash_match:{' '}
              {vm.telemetry.payload_hash_sha256 && vm.telemetry.server_confirmed_hash_sha256
                ? String(vm.telemetry.payload_hash_sha256 === vm.telemetry.server_confirmed_hash_sha256)
                : '—'}
            </li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-hardware">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.hardware', 'Hardware')}</div>
          <p className="mt-2 text-slate-300 font-mono">{vm.hardwareSummary}</p>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-health">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.windowsHealth', 'Windows-Health')}</div>
          <p className="mt-2 text-slate-300 font-mono">{vm.windowsHealthSummary}</p>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-backup">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.backup', 'Backup-Auswahl')}</div>
          <p className="mt-2 text-slate-300 font-mono">{vm.backupSummary}</p>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.completion', 'Abschluss')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li data-testid="windows-rescue-completion-ampel">ampel: {vm.completion.ampel}</li>
            <li>repartition: {vm.repartitionBlocked ? 'blocked' : 'unblocked'}</li>
            <li>dualboot: {vm.dualbootPlanningOnly ? 'planning_only' : '—'}</li>
          </ul>
        </div>
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-[11px] text-slate-400">
          {t('devDashboard.windowsRescue.rawJson', 'Roh-JSON')}
        </summary>
        <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-2 text-[10px] text-slate-400">{vm.rawJson}</pre>
      </details>

      <p className="mt-3 text-[11px] text-slate-500">
        {t(
          'devDashboard.windowsRescue.noAckNoGreen',
          'Kein Grün ohne Telemetrie-ACK und Hash-Bestätigung. Telemetrie ≠ Dateisicherung.',
        )}
      </p>
    </section>
  )
}
