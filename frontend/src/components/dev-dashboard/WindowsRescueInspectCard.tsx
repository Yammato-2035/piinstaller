import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { buildCardViewModelFromOperatorStatus } from '../../lib/devDashboard/windowsRescueInspectReport'
import { buildRescueStickGateViewModel } from '../../lib/devDashboard/rescueStickUsbGate'

export type WindowsRescueInspectCardProps = {
  planningOnly?: boolean
}

export const WindowsRescueInspectCard: React.FC<WindowsRescueInspectCardProps> = ({ planningOnly = true }) => {
  const { t } = useTranslation()
  const vm = useMemo(() => buildCardViewModelFromOperatorStatus(), [])
  const gate = useMemo(() => buildRescueStickGateViewModel(), [])

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
          {t('devDashboard.windowsRescue.awaitingOperator', 'Operator-Hardwarelauf ausstehend — Sample ≠ echte Evidence')}
        </p>
      ) : null}

      <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3 text-xs">
        <div className="rounded border border-amber-800/50 bg-amber-950/20 p-3 md:col-span-2 lg:col-span-3" data-testid="windows-rescue-stick-gate">
          <div className="font-semibold text-amber-200">{t('devDashboard.windowsRescue.stickGate', 'Rescue-Stick (upstream)')}</div>
          <ul className="mt-2 grid gap-1 sm:grid-cols-2 text-slate-300 font-mono">
            <li>iso: {gate.isoStatus}</li>
            <li>verified: {String(gate.isoVerified)}</li>
            <li>usb_written: {gate.usbWritten}</li>
            <li>target_boot: {String(gate.targetBooted)}</li>
            <li>inspect_ok: {String(gate.windowsInspectExecutable)}</li>
            <li className="text-amber-300">blocker: {gate.blockers.join(', ')}</li>
          </ul>
          <p className="mt-2 text-[10px] text-slate-400">{gate.nextOperatorStep}</p>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-operator-run">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.operatorRun', 'Operator-Lauf')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {vm.operatorRun}</li>
            <li>mode: {vm.operatorStatus.operator_mode ?? 'B'}</li>
            <li>real_data: {String(vm.operatorStatus.real_laptop_data_present)}</li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-bitlocker">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.bitlocker', 'BitLocker')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {vm.bitlockerDisplay}</li>
            <li>access: {String(vm.operatorStatus.windows_file_access_allowed)}</li>
            <li>known: {String(vm.operatorStatus.bitlocker_status_known)}</li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-telemetry">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.telemetry', 'Telemetrie')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {vm.telemetry.telemetry_status}</li>
            <li>ack: {String(vm.operatorStatus.telemetry_ack_present)}</li>
            <li>
              hash_match:{' '}
              {vm.telemetry.payload_hash_sha256 && vm.telemetry.server_confirmed_hash_sha256
                ? String(vm.telemetry.payload_hash_sha256 === vm.telemetry.server_confirmed_hash_sha256)
                : String(vm.operatorStatus.hash_match)}
            </li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-hardware">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.hardware', 'Hardware')}</div>
          <p className="mt-2 text-slate-300 font-mono">{vm.hardwareSummary}</p>
          <p className="mt-1 text-[10px] text-slate-500">{vm.operatorStatus.expected_hardware_profile}</p>
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
            <li>dualboot: planning_only</li>
          </ul>
        </div>
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-[11px] text-slate-400">
          {t('devDashboard.windowsRescue.stickGateRaw', 'Roh-JSON Stick-Gate')}
        </summary>
        <pre className="mt-2 max-h-32 overflow-auto rounded bg-slate-950 p-2 text-[10px] text-slate-400">{gate.rawJson}</pre>
      </details>

      <details className="mt-2">
        <summary className="cursor-pointer text-[11px] text-slate-400">
          {t('devDashboard.windowsRescue.rawJson', 'Roh-JSON (Status / kein Sample als Evidence)')}
        </summary>
        <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-2 text-[10px] text-slate-400">{vm.rawJson}</pre>
      </details>

      <details className="mt-2">
        <summary className="cursor-pointer text-[11px] text-slate-500">
          {t('devDashboard.windowsRescue.sampleOnly', 'Planungs-Sample (nicht als echte Evidence)')}
        </summary>
        <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-950 p-2 text-[10px] text-slate-500">
          {JSON.stringify(vm.sampleReport, null, 2)}
        </pre>
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
