# Developer QEMU Autopilot Enable — Root Cause

**Datum:** 2026-06-03

## Befund

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Autopilot-Service-Datei | **yes** (Profil-Overlay + includes.chroot) |
| Hook 090 vorhanden | **yes** (`config/hooks/normal/090-enable-qemu-smoke-autopilot.hook.chroot`) |
| Hook 090 ausführbar | **yes** (0755 via rsync) |
| Hook-Kontext | **chroot** (`.hook.chroot`) — korrekt |
| `systemctl enable` im Chroot | **unzuverlässig** (systemd offline; kein wants-Symlink in Squashfs) |

## Vergleich: was funktioniert

`prepare-controlled-live-build-tree.sh` erzeugt **statische** wants-Symlinks für:

- `setuphelfer-backend.service`
- `setuphelfer.service`

→ diese erscheinen in der Squashfs unter `multi-user.target.wants/`.

Autopilot hatte **nur** Hook 090 mit `systemctl enable … || true` — ohne statischen Symlink.

## Root-Cause-Klassifikation

**`systemctl_enable_not_effective_in_chroot`**

Mitwirkend: **`prepare_profile_not_materializing_wants`** (Autopilot nicht wie Backend/Service per Prepare-Symlink abgesichert).

Hook 090 bleibt als sekundärer Versuch; primärer Fix ist statischer wants-Symlink.
