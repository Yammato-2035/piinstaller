# Wissensbasis: Rescue Core Facades

Rettungsstick- und Rescue-Agent-Code nutzt **nur**:

- `core.storage_facade` — Blockgeräte, Mount-Infos, Backup-Ziel-Klassifikation
- `core.mount_facade` — readonly-Mount-Pläne, Quelle/Ziel-Validierung
- `core.safety_facade` — Write-Guard für backup/restore/live/rescue-Kontexte

## Kontexte

`live`, `rescue`, `cloudserver_future` — Entscheidungen über `build_safety_decision` / write_guard.

## Anti-Pattern

Eigene `subprocess`+`lsblk`/`findmnt` in neuen Rescue-Modulen → Boundary-Warnung.

## ISO-Vorbereitung

Facades müssen vor ISO-Build grün sein (pytest); Deploy-Drift separat lösen.
