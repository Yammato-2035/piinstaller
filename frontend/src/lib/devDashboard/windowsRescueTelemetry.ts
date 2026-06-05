export type TriState = 'yes' | 'no' | 'unknown'
export type VolumeLockStatus = 'unlocked' | 'locked' | 'suspended' | 'unknown'

export type BitLockerInspectState = {
  bitlocker_active: TriState
  device_encryption_active: TriState
  volume_lock_status: VolumeLockStatus
  recovery_key_required: TriState
  windows_partition_encrypted: boolean | null
  data_partition_encrypted: boolean | null
  user_profiles_accessible: boolean | null
}

export type TelemetryStatus =
  | 'not_created'
  | 'queued_local'
  | 'sending'
  | 'sent_unconfirmed'
  | 'acknowledged'
  | 'failed_retryable'
  | 'failed_final'
  | 'blocked_no_network'
  | 'blocked_missing_consent'
  | 'blocked_policy'

export type TelemetryTransportState = {
  telemetry_status: TelemetryStatus
  server_ack_id: string | null
  server_ack_at: string | null
  payload_hash_sha256: string | null
  server_confirmed_hash_sha256: string | null
  retry_count: number
  last_error: string | null
  queue_depth?: number
}

const MVP_ACTION_FLAGS = {
  write_action_allowed: false,
  repair_action_allowed: false,
  partition_action_allowed: false,
} as const

export function mvpActionFlags() {
  return { ...MVP_ACTION_FLAGS }
}

/** BitLocker must be checked before any file/registry access — never assume inactive. */
export function canAccessWindowsFiles(state: BitLockerInspectState): boolean {
  if (state.bitlocker_active === 'unknown' || state.device_encryption_active === 'unknown') return false
  if (state.volume_lock_status === 'locked' || state.volume_lock_status === 'unknown') return false
  if (state.volume_lock_status === 'suspended') return false
  if (state.recovery_key_required === 'yes') return false
  if (state.recovery_key_required === 'unknown') return false
  if (state.user_profiles_accessible === false) return false
  return true
}

export function canRunBackup(state: BitLockerInspectState): boolean {
  return canAccessWindowsFiles(state)
}

export function classifyBitLockerCodes(state: BitLockerInspectState): string[] {
  const codes: string[] = []
  if (state.bitlocker_active === 'no' && state.device_encryption_active === 'no' && state.volume_lock_status === 'unlocked') {
    codes.push('WIN-BITLOCKER-001')
  }
  if (state.volume_lock_status === 'locked' || (state.bitlocker_active === 'yes' && state.volume_lock_status === 'locked')) {
    codes.push('WIN-BITLOCKER-002')
  }
  if (state.device_encryption_active === 'yes' || (state.device_encryption_active === 'unknown' && state.bitlocker_active === 'unknown')) {
    if (!codes.includes('WIN-BITLOCKER-003')) codes.push('WIN-BITLOCKER-003')
  }
  if (state.recovery_key_required === 'yes') {
    codes.push('WIN-BITLOCKER-004')
  }
  if (
    state.bitlocker_active === 'unknown' &&
    (state.volume_lock_status === 'unknown' || state.user_profiles_accessible === false)
  ) {
    codes.push('WIN-BITLOCKER-005')
  }
  if (state.volume_lock_status === 'suspended') {
    codes.push('WIN-BITLOCKER-006')
  }
  if (!codes.length && !canAccessWindowsFiles(state)) {
    codes.push('WIN-BITLOCKER-005')
  }
  return [...new Set(codes)]
}

export type InspectCompletionAmpel = 'green' | 'yellow' | 'red'

/** No green without server ACK and matching hash. */
export function evaluateInspectCompletion(
  inspectReportCreated: boolean,
  transport: TelemetryTransportState,
): { ampel: InspectCompletionAmpel; classification: string } {
  if (!inspectReportCreated) {
    return { ampel: 'yellow', classification: 'inspect_report_missing' }
  }
  if (transport.telemetry_status === 'acknowledged' && transport.server_ack_id) {
    if (
      transport.payload_hash_sha256 &&
      transport.server_confirmed_hash_sha256 &&
      transport.payload_hash_sha256 !== transport.server_confirmed_hash_sha256
    ) {
      return { ampel: 'red', classification: 'telemetry_hash_mismatch' }
    }
    if (transport.payload_hash_sha256 && transport.server_confirmed_hash_sha256) {
      return { ampel: 'green', classification: 'inspect_and_telemetry_acknowledged' }
    }
    if (transport.payload_hash_sha256 && !transport.server_confirmed_hash_sha256) {
      return { ampel: 'yellow', classification: 'telemetry_ack_without_hash_confirm' }
    }
    return { ampel: 'green', classification: 'inspect_and_telemetry_acknowledged' }
  }
  if (
    ['queued_local', 'sending', 'sent_unconfirmed', 'failed_retryable', 'blocked_no_network'].includes(
      transport.telemetry_status,
    )
  ) {
    return { ampel: 'yellow', classification: 'telemetry_not_delivered' }
  }
  if (transport.telemetry_status === 'failed_final' || transport.telemetry_status === 'blocked_policy') {
    return { ampel: 'red', classification: 'telemetry_failed_final' }
  }
  return { ampel: 'yellow', classification: 'telemetry_not_delivered' }
}

export function isRepartitionBlocked(
  backupVerified: boolean,
  transport: TelemetryTransportState,
  bitlocker: BitLockerInspectState,
): boolean {
  if (!backupVerified) return true
  const completion = evaluateInspectCompletion(true, transport)
  if (completion.ampel !== 'green') return true
  if (!canAccessWindowsFiles(bitlocker)) return true
  return false
}

const FORBIDDEN_TELEMETRY_KEYS = [
  'password',
  'cookie',
  'token',
  'private_key',
  'ssh_key',
  'file_content',
  'document_content',
] as const

/** Privacy guard: reject payloads containing forbidden key names or file content fields. */
export function privacyGuardBlocksTelemetry(payload: Record<string, unknown>): string | null {
  const json = JSON.stringify(payload).toLowerCase()
  for (const key of FORBIDDEN_TELEMETRY_KEYS) {
    if (json.includes(`"${key}"`)) return 'TELEMETRY-PRIVACY-001'
  }
  if (payload.contains_personal_data === true && payload.operator_consent_state !== 'granted') {
    return 'TELEMETRY-CONSENT-001'
  }
  return null
}
