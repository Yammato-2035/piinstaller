/**
 * Lokaler Fallback wenn das Backend nicht erreichbar ist — gleiche Semantik wie
 * interpret_v1._rule_system_backend_unreachable (key_v1), siehe docs/architecture/diagnose_companion.md.
 */

import type { DiagnosisRecord } from '../types/diagnosis'

export type BackendErrorReason = 'timeout' | 'connection' | 'other' | null | undefined

const STEP_KEYS = [
  'diagnosis.codes.system.shared.actions.check_network',
  'diagnosis.codes.system.shared.actions.check_server_url',
  'diagnosis.codes.system.shared.actions.retry_or_logs',
] as const

function baseConnectivity(
  diagnosisId: string,
  diagnosisCode: string,
  reason: BackendErrorReason,
  technical: string,
  severity: 'high' | 'medium',
  confidence: number,
  companion: DiagnosisRecord['companion_mode'],
  titleKey: string,
  userKey: string,
  titleEn: string,
  userEn: string,
  stepsEn: [string, string, string],
): DiagnosisRecord {
  return {
    schema_version: '2',
    interpreter_version: 'v1-local',
    diagnosis_id: diagnosisId,
    diagnosis_code: diagnosisCode,
    localization_model: 'key_v1',
    module: 'system',
    event: 'backend_unreachable',
    diagnose_type: 'connectivity',
    severity,
    confidence,
    title_key: titleKey,
    user_message_key: userKey,
    suggested_action_keys: [...STEP_KEYS],
    title: titleEn,
    user_message: userEn,
    technical_summary: technical,
    suggested_actions: [...stepsEn],
    quick_fix_available: false,
    source_event: { area: 'system', event_type: 'backend_unreachable', reason: reason ?? 'other' },
    area: 'system',
    beginner_safe: true,
    companion_mode: companion,
    docs_refs: ['docs/architecture/diagnose_companion.md', 'docs/user/QUICKSTART.md'],
    faq_refs: [],
    kb_refs: [],
  }
}

export function localBackendDiagnosis(
  reason: BackendErrorReason,
  options: { technical: string },
): DiagnosisRecord {
  const technical = options.technical
  if (reason === 'timeout') {
    return baseConnectivity(
      'system.backend_timeout',
      'system.backend_timeout',
      reason,
      technical,
      'high',
      0.85,
      'warning',
      'diagnosis.codes.system.backend_timeout.title',
      'diagnosis.codes.system.backend_timeout.user_summary',
      'Server timed out',
      'The connection hit a timeout; the device or network may be overloaded or unreachable.',
      [
        'Check LAN/WLAN and same subnet.',
        'Verify server URL in settings.',
        'Retry later; on Pi check power and storage.',
      ],
    )
  }
  if (reason === 'connection') {
    return baseConnectivity(
      'system.backend_connection',
      'system.backend_connection',
      reason,
      technical,
      'high',
      0.88,
      'warning',
      'diagnosis.codes.system.backend_connection.title',
      'diagnosis.codes.system.backend_connection.user_summary',
      'Server unreachable',
      'No TCP connection; wrong URL, stopped service, or a firewall in between.',
      [
        'Check whether the service runs on the target device.',
        'Match URL/port with the setup guide.',
        'Briefly review firewall rules between machines (do not disable permanently).',
      ],
    )
  }
  return baseConnectivity(
    'system.backend_other',
    'system.backend_other',
    reason,
    technical,
    'medium',
    0.5,
    'caution',
    'diagnosis.codes.system.backend_other.title',
    'diagnosis.codes.system.backend_other.user_summary',
    'Unexpected connection error',
    'Connection failed; verify settings and device reachability.',
    [
      'Check settings and server URL.',
      'Reload the page; if it persists use logs or support.',
      'Review network path between browser and device.',
    ],
  )
}
