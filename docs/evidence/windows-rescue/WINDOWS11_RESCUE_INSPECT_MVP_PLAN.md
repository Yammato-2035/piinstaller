# Windows 11 Rescue Inspect — MVP Plan

**Datum:** 2026-06-05  
**HEAD:** `6c9a05b`  
**Phase:** planning_only (kein HW-Lauf in diesem Prompt)

## MVP-Umfang

| Komponente | Status |
|------------|--------|
| JSON-Schema | `windows_inspect.schema.json` |
| Sample | `windows_inspect_sample.json` |
| Diagnosekatalog | `windows_inspect_diagnostic_codes.json` (17 Codes) |
| KB | `docs/knowledge-base/windows-rescue/*` |
| Roadmap-Track | `windows-laptop-rescue-inspect` |
| Dashboard UI | Roadmap-Filter (DCC); Windows-Panel später |

## Nächste Implementierungsschritte (WINDOWS11_RESCUE_INSPECT_MVP)

1. Read-only Mount-Plan-Skript (Operator-Terminal, nicht Agent-sudo)
2. Offline-Registry-Reader-Stub + pytest-Klassifikation
3. Rescue-Dashboard-Panel für Inspect-Report (read-only)
4. Backup-Manifest Dry-Run Export

## Sicherheit

`safety.write_actions_allowed=false` immer. Cloud `dry_run_only=true`.
