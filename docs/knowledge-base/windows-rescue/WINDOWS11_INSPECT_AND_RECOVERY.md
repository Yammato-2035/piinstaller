# KB — Windows 11 Pro Laptop Inspect & Recovery (read-only)

## Zweck

Rettungsstick read-only: Windows-11-Pro-Laptop (inkl. Beta/Insider) untersuchen, strukturiert dokumentieren, im Dashboard anzeigen — **ohne** Reparatur, **ohne** NTFS-Schreiben.

## Sicherheit (verbindlich)

| Regel | Wert |
|-------|------|
| Mount-Modus | read-only |
| `write_actions_allowed` | `false` |
| BitLocker | vor jedem Dateizugriff prüfen; unknown/locked → blockiert |
| Telemetrie | nur `diagnostic_metadata`; Server-ACK + Hash-Pflicht; kein Grün ohne ACK |
| Cloud-Upload | Dry-Run/Manifest nur; keine Credentials im Repo |
| Dualboot/Partitionierung | blockiert bis Backup verifiziert **und** Telemetrie acknowledged |

## Schema & Codes

- `docs/evidence/windows-rescue/windows_inspect.schema.json`
- `docs/evidence/windows-rescue/windows_rescue_telemetry.schema.json`
- `docs/evidence/windows-rescue/windows_inspect_diagnostic_codes.json`
- `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md`

## Track

Roadmap: `windows-laptop-rescue-inspect` — Next Prompt: `WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN`

Handoff (Stub): `docs/evidence/windows-rescue/WINDOWS11_RESCUE_OPERATOR_READONLY_SCAN_HANDOFF.md`  
Operator HW Run: `docs/evidence/windows-rescue/WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN.md`  
Status: `docs/evidence/windows-rescue/operator_hardware_run_status_latest.json`

## Abgrenzung

Telemetrie ≠ Dateisicherung. Nicht vermischen mit: Restore-E2E, USB-Write, Repartition-Execution, Controlled Command Runner.
