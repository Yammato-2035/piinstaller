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

/** Backend: models.diagnosis.LocalizationModel */
export type DiagnosisLocalizationModel = 'legacy' | 'key_v1'

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

  /** key_v1: Frontend übersetzt über *_key; legacy: Freitext in title/user_message/suggested_actions */
  localization_model?: DiagnosisLocalizationModel
  diagnosis_code?: string | null
  module?: string | null
  event?: string | null
  title_key?: string | null
  user_message_key?: string | null
  technical_summary_key?: string | null
  suggested_action_keys?: string[] | null
  docs_refs?: string[]
  faq_refs?: string[]
  kb_refs?: string[]
  evidence?: Record<string, unknown> | null
  question_path?: string[] | null
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
