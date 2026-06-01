# Diagnose-Export (Development Control Center)

## Zweck

Lab- und QEMU-Smoke-Daten als **redigierter**, kopierbarer Block für Analyse in Cursor oder ChatGPT — ohne manuelles Zusammensuchen aus Fleet API, Serial, Autopilot-JSON und Devserver.

## Nutzung (UI)

1. Development Control Center → Tab **Telemetry** → **Lab Sessions**
2. Session aufklappen
3. Buttons:
   - **Summary kopieren** — Kurztext
   - **Diagnostics JSON kopieren** — vollständiges Export-JSON
   - **Markdown kopieren** — Bericht für Chat/Tickets

Warnhinweis: *Interne Entwicklungsdaten. Nicht öffentlich teilen.*

## API (lokal)

```http
GET /api/dev-diagnostics/qemu-smokes/{run_id}/export
GET /api/dev-diagnostics/qemu-smokes/{run_id}/markdown
GET /api/dev-diagnostics/qemu-smokes/{run_id}/evidence-index
GET /api/dev-diagnostics/fleet-sessions/{session_id}/export
```

Standard: `redacted=true`. Unredigiert nur mit  
`?redacted=false&operator_confirm_unredacted_local_only=true`.

## Keine Steuerfunktionen

Der Export startet **kein** QEMU, kein Backup, kein Deploy.
