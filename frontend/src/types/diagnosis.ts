/**
 * Spiegel von backend/models/diagnosis.py (JSON).
 * Bei Schema-Änderungen backend schema_version prüfen.
 */

export type CompanionMode =
  | 'info'
  | 'caution'
  | 'warning'
  | 'blocked'
  | 'recommendation'
  | 'guided_step'

export type DiagnoseType =
  | 'connectivity'
  | 'permission'
  | 'configuration'
  | 'security'
  | 'backup_restore'
  | 'service'
  | 'unknown'

export type DiagnosisSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical'

export interface DiagnosisRecord {
  schema_version: string
  interpreter_version: string
  diagnosis_id: string
  diagnose_type: DiagnoseType
  severity: DiagnosisSeverity
  confidence: number
  title: string
  user_message: string
  technical_summary: string
  suggested_actions: string[]
  quick_fix_available: boolean
  source_event: Record<string, unknown>
  area: string
  beginner_safe: boolean
  companion_mode: CompanionMode
}

export interface DiagnosisInterpretRequest {
  area: string
  event_type: string
  message?: string | null
  http_status?: number | null
  api_status?: string | null
  request_id?: string | null
  extra?: Record<string, unknown>
}
