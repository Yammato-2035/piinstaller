# Developer QEMU Rebuild — Cleanup After Result

**Datum:** 2026-06-02

## Cleanup-Ausführung (Agent-Session)

| Feld | Wert |
|------|------|
| `sudo … --operator-confirm-clean` | **fehlgeschlagen** (sudo Passwort/TTY in Agent-Session) |
| clean_exit | **1** (nicht angewendet) |

## Zustand nach Dry-Run / ohne erfolgreichen Operator-Clean

| Prüfpunkt | Ergebnis |
|-----------|----------|
| root-owned top-level artifacts entfernt | **no** (7 Dateien weiterhin root:root) |
| stale ISO/squashfs | **keine** im Tree (nur .contents/.packages/wget-log*) |
| aktive Mounts | **none** (`findmnt` leer) |

## Operator-Aktion erforderlich

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

Erwartung: 7× `REMOVED`, `clean_exit=0`.

## Status

**cleanup_incomplete** — Build würde ohne sudo-Clean erneut **LB_EXIT=34** liefern.
