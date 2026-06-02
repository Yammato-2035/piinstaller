# Developer QEMU Autopilot Enable Fix — Result

**Datum:** 2026-06-03

## Zusammenfassung

| Aspekt | Ergebnis |
|--------|----------|
| Root Cause | `systemctl enable` im Chroot wirkungslos |
| Fix | Statischer wants-Symlink (developer-qemu only) |
| Prepare Exit | 0 |
| Wants-Symlink | **yes** |
| Validator erweitert | **yes** |
| Tests | 8 OK |
| Alter ISO (3ee02b36…) | Validator Exit **12** (wants fehlt — erwartet) |
| Neuer ISO-Build | **no** (dieser Lauf) |
| QEMU | **no** |

## Readiness

**`ready_for_developer_qemu_iso_rebuild_operator_run`**

Vor Rebuild: Operator `sudo clean` (entfernt stale binary/), optional validate Exit 0, dann Build mit `--profile developer-qemu`.

## Nächster Schritt

1. **DEVELOPER QEMU ISO REBUILD OPERATOR RUN**
2. Artefakt verifizieren (Squashfs-Validator Exit 0 inkl. Autopilot-wants)
3. **QEMU Guest Agent Smoke Operator Run, NO USB**

Alter Rebuild-Verify (`3ee02b36…`) bleibt historisch `review_required` bis ersetzt.
