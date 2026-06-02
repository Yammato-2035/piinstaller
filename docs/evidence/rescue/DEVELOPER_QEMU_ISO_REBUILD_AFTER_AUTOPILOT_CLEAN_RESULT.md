# Developer QEMU ISO Rebuild After Autopilot Fix — Clean Result

**Datum:** 2026-06-03

## Dry-Run

| Feld | Wert |
|------|------|
| Exit | **0** |
| Targets | 13 (inkl. binary/, binary.hybrid.iso, chroot/) |
| Root-owned | 11 |

## Clean Apply (Agent-Session)

| Feld | Wert |
|------|------|
| Exit | **1** (sudo Passwort/TTY fehlt) |
| Alte ISO entfernt | **no** |
| Alte Squashfs entfernt | **no** |
| Aktive Mounts | **none** |

## Status

**blocked** — Operator-Terminal erforderlich:

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```
