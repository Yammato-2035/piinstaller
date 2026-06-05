import type { BitLockerInspectState, TelemetryTransportState } from './windowsRescueTelemetry'
import { evaluateInspectCompletion, isRepartitionBlocked } from './windowsRescueTelemetry'
import operatorSample from '../../../../docs/evidence/windows-rescue/windows_inspect_operator_readonly_sample.json'

export type WindowsInspectOperatorReport = typeof operatorSample

export function loadOperatorReadonlySample(): WindowsInspectOperatorReport {
  return operatorSample as WindowsInspectOperatorReport
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

function mapTelemetry(report: WindowsInspectOperatorReport): TelemetryTransportState {
  const tel = report.telemetry
  const ack = String(tel?.ack_status || 'not_created')
  const localHash = tel?.local_report_hash || null
  const hashMatch = tel?.hash_match
  return {
    telemetry_status: ack as TelemetryTransportState['telemetry_status'],
    server_ack_id: ack === 'acknowledged' ? 'sample-ack' : null,
    server_ack_at: ack === 'acknowledged' ? report.generated_at : null,
    payload_hash_sha256: localHash,
    server_confirmed_hash_sha256: hashMatch === true ? localHash : hashMatch === false ? 'mismatch' : null,
    retry_count: ack === 'queued_local' ? 1 : 0,
    last_error: ack === 'queued_local' ? 'TELEMETRY-NETWORK-001' : null,
    queue_depth: ack === 'queued_local' ? 1 : 0,
  }
}

export type WindowsRescueCardViewModel = {
  report: WindowsInspectOperatorReport | null
  bitlocker: BitLockerInspectState
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

export function buildCardViewModel(report: WindowsInspectOperatorReport | null): WindowsRescueCardViewModel {
  if (!report) {
    return {
      report: null,
      bitlocker: mapBitlockerStatus('unknown'),
      telemetry: {
        telemetry_status: 'not_created',
        server_ack_id: null,
        server_ack_at: null,
        payload_hash_sha256: null,
        server_confirmed_hash_sha256: null,
        retry_count: 0,
        last_error: null,
        queue_depth: 0,
      },
      inspectReportCreated: false,
      backupVerified: false,
      hardwareSummary: '—',
      windowsHealthSummary: 'no_windows_inspect_report_available',
      backupSummary: '—',
      repartitionBlocked: true,
      dualbootPlanningOnly: true,
      completion: evaluateInspectCompletion(false, {
        telemetry_status: 'not_created',
        server_ack_id: null,
        server_ack_at: null,
        payload_hash_sha256: null,
        server_confirmed_hash_sha256: null,
        retry_count: 0,
        last_error: null,
      }),
      rawJson: '{}',
    }
  }

  const bitlocker = mapBitlockerStatus(report.bitlocker?.status)
  const telemetry = mapTelemetry(report)
  const backupVerified = report.backup_selection?.backup_verified === true
  const completion = evaluateInspectCompletion(true, telemetry)
  const repartitionBlocked = isRepartitionBlocked(backupVerified, telemetry, bitlocker)

  const hw = report.hardware
  const hardwareSummary = [hw?.cpu_vendor, hw?.gpu_vendor, `${(hw?.nvme_devices?.length ?? 0)}× NVMe`]
    .filter(Boolean)
    .join(' / ')

  const wh = report.windows_health
  const windowsHealthSummary = `explorer: ${wh?.explorer_shell_status ?? '—'}; registry: ${String(wh?.registry_available ?? '—')}`

  const cand = report.backup_selection?.candidate_user_dirs?.length ?? 0
  const backupSummary = `dry_run; candidates: ${cand}; selected: ${report.backup_selection?.selected_paths?.length ?? 0}`

  return {
    report,
    bitlocker,
    telemetry,
    inspectReportCreated: true,
    backupVerified,
    hardwareSummary,
    windowsHealthSummary,
    backupSummary,
    repartitionBlocked,
    dualbootPlanningOnly: report.dualboot_readiness?.planning_only !== false,
    completion,
    rawJson: JSON.stringify(report, null, 2),
  }
}

export function buildCardViewModelFromSample(): WindowsRescueCardViewModel {
  return buildCardViewModel(loadOperatorReadonlySample())
}
