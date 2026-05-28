# Rescue ISO — Mount-Cleanup-Plan (BUILD_TREE only)

**BUILD_TREE:** `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live`

## Regeln

1. `findmnt -R "$BUILD_TREE"` — nur Pfade unter Prefix behandeln.
2. Tiefste Mounts zuerst `umount` / `umount -l`.
3. **Kein** `rm -rf` auf `chroot`, solange Mounts existieren.
4. Pfade außerhalb Prefix → **STOP** (Exit 40).

## Aktueller read-only Befund

- Keine aktiven Mounts unter BUILD_TREE (Stand Triage).
- Beschädigter `chroot/`-Rest (`proc` leer, kein `/usr/bin/env`) — Entfernung erfordert **sudo** (`root`-owned).

JSON: `rescue_iso_chroot_mount_cleanup_plan_latest.json`
