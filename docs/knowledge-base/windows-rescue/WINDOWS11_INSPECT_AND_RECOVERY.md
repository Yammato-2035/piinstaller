# KB — Windows 11 Pro Laptop Inspect & Recovery (read-only)

## Zweck

Rettungsstick read-only: Windows-11-Pro-Laptop (inkl. Beta/Insider) untersuchen, strukturiert dokumentieren, im Dashboard anzeigen — **ohne** Reparatur, **ohne** NTFS-Schreiben.

## Sicherheit (verbindlich)

| Regel | Wert |
|-------|------|
| Mount-Modus | read-only |
| `write_actions_allowed` | `false` |
| BitLocker locked | nicht brutal mounten; Recovery Key nur Operator-seitig |
| Cloud-Upload | Dry-Run/Manifest nur; keine Credentials im Repo |
| Dualboot/Partitionierung | Planung nur |

## Schema & Codes

- `docs/evidence/windows-rescue/windows_inspect.schema.json`
- `docs/evidence/windows-rescue/windows_inspect_diagnostic_codes.json`
- `docs/evidence/windows-rescue/windows_inspect_sample.json`

## Track

Roadmap: `windows-laptop-rescue-inspect` — Next Prompt: `WINDOWS11_RESCUE_INSPECT_MVP`

## Abgrenzung

Nicht vermischen mit: Restore-E2E, USB-Write, Backup-Release-Gate, Monolith-Split, Controlled Command Runner.
