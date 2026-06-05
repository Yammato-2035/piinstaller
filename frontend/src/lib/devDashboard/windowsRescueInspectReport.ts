import type { BitLockerInspectState, TelemetryTransportState } from './windowsRescueTelemetry'
import { evaluateInspectCompletion, isRepartitionBlocked } from './windowsRescueTelemetry'
import operatorStatus from '../../../../docs/evidence/windows-rescue/operator_hardware_run_status_latest.json'
import operatorSample from '../../../../docs/evidence/windows-rescue/windows_inspect_operator_readonly_sample.json'

export type OperatorHardwareRunStatus = typeof operatorStatus
export type WindowsInspectOperatorReport = typeof operatorSample & {
  data_classification?: string
  source?: string
}

export function loadOperatorHardwareRunStatus(): OperatorHardwareRunStatus {
  return operatorStatus as OperatorHardwareRunStatus
}

export function loadOperatorReadonlySample(): WindowsInspectOperatorReport {
  return operatorSample as WindowsInspectOperatorReport
}

export type OperatorHardwareRunDisplay = 'missing' | 'available' | 'ingested'

export function operatorHardwareRunDisplay(status: OperatorHardwareRunStatus): OperatorHardwareRunDisplay {
  if (status.status === 'operator_hardware_run_ingested' && status.real_laptop_data_present) return 'ingested'
  if (status.status === 'awaiting_operator_hardware_run') return 'missing'
  return 'available'
}

function mapBitlockerStatus(status: string | undefined): BitLockerInspectState {
  const s = String(status || 'unknown').toLowerCase()
  const active: BitLockerInspectState['bitlocker_active'] =
    s === 'not_detected' ? 'no' : s === 'unknown' ? 'unknown' : s === 'locked' ? 'yes' : 'unknown'
  return {
    bitlocker_active: active,
    device_encryption_active: s === 'not_detected' ? 'no' : 'unknown',
    volume_lock_status: s === 'locked' ? 'locked' : s === 'unlocked' ? 'unlocked' : 'unknown',
    recovery_key_required: s === 'locked' ? 'yes' : 'unknown',
    windows_partition_encrypted: s === 'locked' ? true : null,
    data_partition_encrypted: null,
    user_profiles_accessible: s === 'not_detected' || s === 'unlocked' ? true : false,
  }
}

function mapTelemetryFromReport(report: WindowsInspectOperatorReport): TelemetryTransportState {
  const tel = report.telemetry
  const ack = String(tel?.ack_status || 'not_created')
  const localHash = tel?.local_report_hash || null
  const hashMatch = tel?.hash_match
  return {
    telemetry_status: ack as TelemetryTransportState['telemetry_status'],
    server_ack_id: tel?.server_ack_id ?? (ack === 'acknowledged' ? 'sample-ack' : null),
    server_ack_at: ack === 'acknowledged' ? report.generated_at : null,
    payload_hash_sha256: localHash,
    server_confirmed_hash_sha256: hashMatch === true ? localHash : hashMatch === false ? 'mismatch' : null,
    retry_count: ack === 'queued_local' ? 1 : 0,
    last_error: ack === 'queued_local' ? 'TELEMETRY-NETWORK-001' : null,
    queue_depth: ack === 'queued_local' ? 1 : 0,
  }
}

function mapTelemetryFromStatus(status: OperatorHardwareRunStatus): TelemetryTransportState {
  const ack = status.telemetry_ack_present ? 'acknowledged' : 'not_created'
  return {
    telemetry_status: ack as TelemetryTransportState['telemetry_status'],
    server_ack_id: status.telemetry_ack_present ? 'operator-ack' : null,
    server_ack_at: null,
    payload_hash_sha256: null,
    server_confirmed_hash_sha256: status.hash_match ? 'matched' : null,
    retry_count: 0,
    last_error: null,
    queue_depth: 0,
  }
}

export type WindowsRescueCardViewModel = {
  operatorRun: OperatorHardwareRunDisplay
  operatorStatus: OperatorHardwareRunStatus
  report: WindowsInspectOperatorReport | null
  sampleReport: WindowsInspectOperatorReport
  bitlocker: BitLockerInspectState
  bitlockerDisplay: string
  telemetry: TelemetryTransportState
  inspectReportCreated: boolean
  backupVerified: boolean
  hardwareSummary: string
  windowsHealthSummary: string
  backupSummary: string
  repartitionBlocked: boolean
  dualbootPlanningOnly: boolean
  completion: ReturnType<typeof evaluateInspectCompletion>
  rawJson: string
}

export function buildCardViewModelFromOperatorStatus(
  status: OperatorHardwareRunStatus = loadOperatorHardwareRunStatus(),
  sample: WindowsInspectOperatorReport = loadOperatorReadonlySample(),
): WindowsRescueCardViewModel {
  const operatorRun = operatorHardwareRunDisplay(status)
  const report =
    operatorRun === 'ingested' && status.real_laptop_data_present
      ? sample
      : null

  const bitlockerDisplay = status.bitlocker_status_known
    ? report?.bitlocker?.status ?? 'unknown'
    : 'unknown'
  const bitlocker = mapBitlockerStatus(bitlockerDisplay)

  const telemetry =
    report != null ? mapTelemetryFromReport(report) : mapTelemetryFromStatus(status)
  const inspectReportCreated = operatorRun === 'ingested'
  const backupVerified = report?.backup_selection?.backup_verified === true
  const completion =
    operatorRun === 'ingested' && report
      ? evaluateInspectCompletion(true, telemetry)
      : {
          ampel: status.completion_ampel as 'green' | 'yellow' | 'red',
          classification: status.completion_classification,
        }

  const repartitionBlocked =
    operatorRun !== 'ingested' ||
    isRepartitionBlocked(backupVerified, telemetry, bitlocker) ||
    status.completion_ampel !== 'green'

  const hw = report?.hardware ?? sample.hardware
  const hardwareSummary = [hw?.cpu_vendor, hw?.gpu_vendor, `${(hw?.nvme_devices?.length ?? 0)}× NVMe`]
    .filter(Boolean)
    .join(' / ')

  const wh = report?.windows_health ?? sample.windows_health
  const windowsHealthSummary =
    operatorRun === 'ingested'
      ? `explorer: ${wh?.explorer_shell_status ?? '—'}; registry: ${String(wh?.registry_available ?? '—')}`
      : `awaiting_operator_run; file_access: ${String(status.windows_file_access_allowed)}`

  const cand = (report ?? sample).backup_selection?.candidate_user_dirs?.length ?? 0
  const backupSummary = `dry_run only; candidates: ${cand}`

  return {
    operatorRun,
    operatorStatus: status,
    report,
    sampleReport: sample,
    bitlocker,
    bitlockerDisplay,
    telemetry,
    inspectReportCreated,
    backupVerified,
    hardwareSummary,
    windowsHealthSummary,
    backupSummary,
    repartitionBlocked,
    dualbootPlanningOnly: true,
    completion,
    rawJson: JSON.stringify(report ?? status, null, 2),
  }
}

/** @deprecated use buildCardViewModelFromOperatorStatus */
export function buildCardViewModelFromSample(): WindowsRescueCardViewModel {
  return buildCardViewModelFromOperatorStatus()
}
