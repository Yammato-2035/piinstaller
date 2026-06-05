# Project Rules — Existing Structure Audit

**Datum:** 2026-06-05  
**Dateiliste:** `project_rules_existing_files_latest.log` (348 Einträge)

## Maßgebliche Roadmap-Dateien

| Datei | Rolle |
|-------|-------|
| `docs/roadmap/STATUS_MATRIX.md` | Ampel-/Status-Übersicht |
| `docs/roadmap/MONOLITH_REFACTOR_PLAN.md` | Monolith-Folgepfade |
| `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.json` | Next-Prompt + Tracks |
| `docs/faq/dev_dashboard_roadmap_faq.md` | FAQ Roadmap/Registry |

## NEXT_PROMPT-Verwaltung

- Primär: `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.json`
- Ergänzend: Closure-Regel in `docs/developer/CURSOR_WORK_RULES.md`
- Registry-FAQ: `docs/faq/dev_dashboard_roadmap_faq.md`

## Wiederkehrende Fehler

| Bereich | Vorher | Nach diesem Lauf |
|---------|--------|------------------|
| Rescue/QEMU | verstreut in Evidence | `docs/knowledge-base/recovery/RESCUE_QEMU_RECURRENT_FAILURES.md` |
| DCC/Ports | `DCC_PORTS_AND_URLS.md`, Evidence | `docs/knowledge-base/dev-dashboard/DCC_PROFILE_AND_PORT_ERRORS.md` |
| Übergreifend | — | `docs/knowledge-base/diagnostics/KNOWN_RECURRENT_ERRORS.md` |

## Wissensdatenbank / FAQ

- `docs/knowledge-base/` (348 Dateien im Audit-Scope)
- `docs/faq/` inkl. `dev_dashboard_roadmap_faq.md`

## Cursor-/Developer-Regeln

- `docs/developer/CURSOR_WORK_RULES.md` — verbindliche Arbeitsregeln
- `.cursor/rules/` — 19+ Regeln inkl. neu `200_ROADMAP_KB_FIRST.md`
- `runtime-phase0-gate.mdc` — Runtime-Gate

## Lücken (vor diesem Lauf)

1. Keine explizite Roadmap-First-Regel mit Pflicht-Updates
2. Keine KB-First-Triage mit Klassifikations-Enum
3. Kein wiederverwendbares Known-Error-Template/Schema
4. `NEXT_PROMPT_SELECTION_LATEST.json` veraltet (2026-05-30)
5. Recurrent errors nicht zentral in KB gebündelt

## Künftig verbindlich zu aktualisieren

1. `docs/roadmap/STATUS_MATRIX.md`
2. `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.json`
3. `docs/knowledge-base/diagnostics/KNOWN_RECURRENT_ERRORS.md` (bei neuem wiederkehrendem Fehler)
4. `docs/developer/CURSOR_WORK_RULES.md` (bei Regeländerung)
5. Evidence unter `docs/evidence/diagnostics/` pro Governance-Lauf
