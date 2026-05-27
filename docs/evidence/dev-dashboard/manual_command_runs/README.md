# Manual Command Runs (read-only Evidence)

Strukturierte Nachweise für **manuelle** Operator-/Cursor-Kommandos — **ohne** Ausführung aus dem Dashboard.

## Regeln

- Eine Datei pro Lauf: `*.json` (Schema: `manual_command_run.schema.json`).
- Chat-Ausschnitte allein reichen **nicht** — `full_log_path` oder bewusst `excerpt_only` mit Hinweis in `notes`.
- `safety_class`: `read_only` | `operator_action` | `forbidden` (forbidden wird im Dashboard rot markiert).
- Keine Secrets in `stdout_excerpt` / `stderr_excerpt`.

## Dashboard

`GET /api/dev-dashboard/manual-command-runs` — read-only Liste, keine POST/Execute-Route.
