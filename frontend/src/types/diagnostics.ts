export type DiagnosticsSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical'
export type DiagnosticsConfidence = 'low' | 'medium' | 'high'
export type DiagnosticsUserLevel = 'beginner' | 'advanced' | 'expert'

export interface DiagnosticsAnalyzeRequest {
  question?: string
  context?: Record<string, unknown>
  signals?: Record<string, unknown>
}

export interface DiagnosticsAnalyzeResponse {
  primary_diagnosis: { id: string; domain: string; severity: DiagnosticsSeverity; confidence: DiagnosticsConfidence } | null
  secondary_diagnoses: Array<{ id: string; domain: string; severity: DiagnosticsSeverity; confidence: DiagnosticsConfidence }>
  severity: DiagnosticsSeverity
  confidence: DiagnosticsConfidence
  messages: Record<DiagnosticsUserLevel, string>
  user_message_beginner: string
  technical_summary: string
  actions_now: string[]
  actions_later: string[]
  recommended_actions: Array<{ id: string; priority: number; text_de: string; text_en: string }>
  safe_auto_actions: string[]
  requires_confirmation: boolean
}
