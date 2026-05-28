# ROADMAP_BACKGROUND_TASK_AND_STANDALONE_DELTA

## Anlass

Strict-Mode Audit nach unerwuenschter Background-/Auto-Kette und gemeldeter Standalone-Sichtbarkeitsprobleme im Developer Control Center.

## Feststellungen

- Governance:
  - Unautorisierte Auto-Background-Kette wurde als Risiko bestaetigt.
  - Aktueller Zustand enthaelt bereits auf `origin/main` liegende Commits aus diesem Verlauf.
  - Neuer Governance-Blocker: `unapproved_background_task_detected`.
- Runtime:
  - Backend-Service aktiv, Port 8000 listening, API-Endpunkte timeouten.
  - Runtime-Status bleibt `blocked`/`hanging`, kein Fake-Green.
- Standalone Control Center:
  - Snapshot im Workspace vorhanden und valide.
  - Ursache fuer "fast leer" im aktiven Betrieb als starke Runtime-/Lieferpfad-Abhaengigkeit dokumentiert.
  - Kein riskanter Schnellfix ohne klare isolierte Frontend-Ursache.

## Roadmap-/Prompt-Delta

- `setuphelfer_roadmap.json`
  - Metadaten aktualisiert (`generated_at`, `source_commit`).
  - Runtime bleibt blockiert; keine gruene Fortschrittsbehauptung.
- `setuphelfer_next_prompts.json`
  - `selected_prompt_id` auf `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF` gesetzt.
- `NEXT_PROMPT_SELECTION_LATEST.json/.md`
  - Auswahl und Begruendung auf Operator-Handoff unter Hang-Bedingung umgestellt.
  - `runtime_gate_blocked_static_analysis_only` auf `true`.

## Empfehlung

- Naechster Prompt: `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF`
- Danach: `BACKEND_RUNTIME_OPERATOR_RESTART_RESULT_INGEST` mit Operator-Loggroundtruth.
