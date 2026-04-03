/**
 * Lokaler Fallback wenn das Backend nicht erreichbar ist — gleiche Semantik wie
 * interpret_v1._rule_system_backend_unreachable (siehe docs/architecture/diagnose_companion.md).
 */

import type { DiagnosisRecord } from '../types/diagnosis'

export type BackendErrorReason = 'timeout' | 'connection' | 'other' | null | undefined

export function localBackendDiagnosis(
  reason: BackendErrorReason,
  strings: {
    title: string
    userMessage: string
    technical: string
    steps: string[]
  },
): DiagnosisRecord {
  const base = {
    schema_version: '1',
    interpreter_version: 'v1-local',
    diagnose_type: 'connectivity' as const,
    technical_summary: strings.technical,
    suggested_actions: strings.steps,
    quick_fix_available: false,
    source_event: { area: 'system', event_type: 'backend_unreachable', reason: reason ?? 'other' },
    area: 'system',
    beginner_safe: true,
  }

  if (reason === 'timeout') {
    return {
      ...base,
      diagnosis_id: 'system.backend_timeout',
      severity: 'high',
      confidence: 0.85,
      title: strings.title,
      user_message: strings.userMessage,
      companion_mode: 'warning',
    }
  }
  if (reason === 'connection') {
    return {
      ...base,
      diagnosis_id: 'system.backend_connection',
      severity: 'high',
      confidence: 0.88,
      title: strings.title,
      user_message: strings.userMessage,
      companion_mode: 'warning',
    }
  }
  return {
    ...base,
    diagnosis_id: 'system.backend_other',
    severity: 'medium',
    confidence: 0.5,
    title: strings.title,
    user_message: strings.userMessage,
    companion_mode: 'caution',
  }
}
