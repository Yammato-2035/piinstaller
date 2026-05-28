# RESCUE-BUILD-CHROOT-CLEANUP-001 — Chroot-/Mount-Cleanup-Fehler

**Datum:** 2026-05-28

## Symptome (letzter Build)

- `rm: das Entfernen von 'chroot/proc/...' ist nicht möglich: Vorgang nicht zulässig`
- `chroot: failed to run command '/usr/bin/env': No such file or directory`
- `LB_EXIT=1`

**Nicht** der isohybrid-Fehler (der war zuvor mit `syslinux-utils` adressiert).

## Read-only Iststand (Agent)

| Check | Wert |
|-------|------|
| `findmnt -R BUILD_TREE` | keine Mounts (jetzt) |
| `chroot/usr/bin/env` | fehlt |
| `chroot/proc` | leeres Verzeichnis-Rest (root-owned) |
| Config `syslinux-utils` | in `setuphelfer.list.binary` |
| `rsvg` include | vorhanden |
| `bootlogo` seed | vorhanden |

## Ursache (wahrscheinlich)

live-build versuchte `chroot/proc` zu löschen, während proc noch als Pseudo-FS aktiv war oder der Chroot bereits halb zerstört war.

## Nächster Schritt

Operator-Cleanup mit sudo (siehe `RESCUE_ISO_CHROOT_MOUNT_CLEANUP_OPERATOR_HANDOFF.md`) — **kein** Build-Retry im Agent.

JSON: `rescue_iso_chroot_cleanup_failure_latest.json`
