import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  evaluateInspectCompletion,
  isRepartitionBlocked,
  type BitLockerInspectState,
  type TelemetryTransportState,
} from '../../lib/devDashboard/windowsRescueTelemetry'

export type WindowsRescueInspectCardProps = {
  bitlocker?: BitLockerInspectState
  telemetry?: TelemetryTransportState
  inspectReportCreated?: boolean
  backupVerified?: boolean
  privacyLevel?: string
  containsPersonalData?: boolean
  planningOnly?: boolean
}

const DEFAULT_BITLOCKER: BitLockerInspectState = {
  bitlocker_active: 'unknown',
  device_encryption_active: 'unknown',
  volume_lock_status: 'unknown',
  recovery_key_required: 'unknown',
  windows_partition_encrypted: null,
  data_partition_encrypted: null,
  user_profiles_accessible: null,
}

const DEFAULT_TELEMETRY: TelemetryTransportState = {
  telemetry_status: 'not_created',
  server_ack_id: null,
  server_ack_at: null,
  payload_hash_sha256: null,
  server_confirmed_hash_sha256: null,
  retry_count: 0,
  last_error: null,
  queue_depth: 0,
}

export const WindowsRescueInspectCard: React.FC<WindowsRescueInspectCardProps> = ({
  bitlocker = DEFAULT_BITLOCKER,
  telemetry = DEFAULT_TELEMETRY,
  inspectReportCreated = false,
  backupVerified = false,
  privacyLevel = 'diagnostic_metadata',
  containsPersonalData = false,
  planningOnly = true,
}) => {
  const { t } = useTranslation()
  const completion = useMemo(
    () => evaluateInspectCompletion(inspectReportCreated, telemetry),
    [inspectReportCreated, telemetry],
  )
  const repartitionBlocked = useMemo(
    () => isRepartitionBlocked(backupVerified, telemetry, bitlocker),
    [backupVerified, telemetry, bitlocker],
  )

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
          {t('devDashboard.windowsRescue.planningOnly', 'Planungs-/Schema-Vorschau — kein HW-Lauf')}
        </p>
      ) : null}

      <div className="mt-3 grid gap-3 md:grid-cols-2 text-xs">
        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-bitlocker">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.bitlocker', 'BitLocker')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>active: {bitlocker.bitlocker_active}</li>
            <li>device_encryption: {bitlocker.device_encryption_active}</li>
            <li>volume: {bitlocker.volume_lock_status}</li>
            <li>recovery_key: {bitlocker.recovery_key_required}</li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3" data-testid="windows-rescue-telemetry">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.telemetry', 'Telemetrie')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>status: {telemetry.telemetry_status}</li>
            <li>queue: {telemetry.queue_depth ?? 0}</li>
            <li>ack_id: {telemetry.server_ack_id ?? '—'}</li>
            <li>ack_at: {telemetry.server_ack_at ?? '—'}</li>
            <li>
              hash_match:{' '}
              {telemetry.payload_hash_sha256 && telemetry.server_confirmed_hash_sha256
                ? String(telemetry.payload_hash_sha256 === telemetry.server_confirmed_hash_sha256)
                : '—'}
            </li>
            {telemetry.last_error ? <li className="text-amber-300">error: {telemetry.last_error}</li> : null}
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.privacy', 'Privacy')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li>level: {privacyLevel}</li>
            <li>personal_data: {String(containsPersonalData)}</li>
          </ul>
        </div>

        <div className="rounded border border-slate-700 bg-slate-950/50 p-3">
          <div className="font-semibold text-cyan-200">{t('devDashboard.windowsRescue.completion', 'Abschluss')}</div>
          <ul className="mt-2 space-y-1 text-slate-300 font-mono">
            <li data-testid="windows-rescue-completion-ampel">ampel: {completion.ampel}</li>
            <li>classification: {completion.classification}</li>
            <li>repartition_blocked: {String(repartitionBlocked)}</li>
          </ul>
        </div>
      </div>

      <p className="mt-3 text-[11px] text-slate-500">
        {t(
          'devDashboard.windowsRescue.noAckNoGreen',
          'Kein Grün ohne Telemetrie-ACK und Hash-Bestätigung. Telemetrie ≠ Dateisicherung.',
        )}
      </p>
    </section>
  )
}
