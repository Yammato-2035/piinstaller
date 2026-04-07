import type { DiagnosisInterpretRequest, DiagnosisRecord } from '../types/diagnosis'

function snapshotSource(req: DiagnosisInterpretRequest): Record<string, unknown> {
  const out: Record<string, unknown> = {
    area: req.area,
    event_type: req.event_type,
    http_status: req.http_status ?? null,
    api_status: req.api_status ?? null,
    request_id: req.request_id ?? null,
    message_excerpt: (req.message || '').slice(0, 400),
  }
  if (req.extra && Object.keys(req.extra).length > 0) {
    out.extra = { ...req.extra }
  }
  return out
}

/**
 * Entspricht `diagnosis.interpret_v1._fallback` in `backend/diagnosis/interpret_v1.py`,
 * wenn `POST /api/diagnosis/interpret` nicht erreichbar ist (Netzwerk, 4xx/5xx, Parse-Fehler).
 */
export function localDiagnosisFallback(req: DiagnosisInterpretRequest): DiagnosisRecord {
  return {
    schema_version: '2',
    interpreter_version: 'v1-local-fallback',
    diagnosis_id: 'unknown.generic',
    diagnosis_code: 'unknown.generic',
    localization_model: 'key_v1',
    module: req.area || 'unknown',
    event: req.event_type,
    title_key: 'diagnosis.codes.unknown.generic.title',
    user_message_key: 'diagnosis.codes.unknown.generic.user_summary',
    suggested_action_keys: ['diagnosis.codes.unknown.generic.actions.expand_technical'],
    diagnose_type: 'unknown',
    severity: 'low',
    confidence: 0.2,
    title: 'No specific diagnosis',
    user_message:
      'No detailed classification for this message; inspect technical details or contact support.',
    technical_summary: (req.message || '').slice(0, 800),
    suggested_actions: ['Expand the technical summary and review manually.'],
    quick_fix_available: false,
    source_event: snapshotSource(req),
    area: req.area || 'unknown',
    beginner_safe: true,
    companion_mode: 'info',
    docs_refs: ['docs/architecture/diagnosis_localization.md'],
    faq_refs: [],
    kb_refs: [],
  }
}
