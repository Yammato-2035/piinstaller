# Diagnosis Data Model

Jeder Diagnosefall (`DiagnosticCase`) enthaelt mindestens:

- `id`, `domain`
- `title_de`, `title_en`
- `summary_de`, `summary_en`
- `severity`, `confidence`
- `user_level_visibility`
- `symptoms`, `detection_sources`, `preconditions`, `checks`
- `root_causes`, `recommended_actions`, `safe_auto_actions`
- `escalation_hint`, `related_docs`, `related_faq`, `tags`
- `requires_confirmation`, `destructive_risk`
- `status_mapping`

Wichtig:

- IDs sind stabil und dienen als Kernreferenz fuer UI, Tests und spaeteres RAG.
- Keine UI-Freitexte als Ersatz fuer den Katalog.
- Safe-Auto-Actions nur fuer nicht-destruktive Schritte.

DIAG-1.1 Ergaenzungen:

- `DiagnosticCase.evidence_counts` (`suspected`, `confirmed`, `refuted`)
- `DiagnosticCase.seen_in_platforms`
- `DiagnosticCase.common_storage_contexts`
- `DiagnosticCase.common_boot_contexts`
- `DiagnosticCase.typical_false_assumptions`

Diese Felder werden nicht blind automatisch geschrieben, sondern aus strukturierten EvidenceRecords aggregiert.
