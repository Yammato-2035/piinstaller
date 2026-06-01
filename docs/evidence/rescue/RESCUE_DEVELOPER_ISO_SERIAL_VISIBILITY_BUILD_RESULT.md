# Developer Rescue ISO — Serial Visibility Build Result

**Stand:** 2026-06-01  
**HEAD:** `cfc8385`  
**Profil:** `developer-qemu`  
**Run-ID:** `rescue_developer_iso_20260601_serial_visibility`  
**Repository:** PUBLIC — **Push blocked**

## Zusammenfassung

| Phase | Ergebnis |
|-------|----------|
| Dependency-Preflight | **OK** — `lb`, `xorriso`, `mksquashfs`, `rsvg-convert`, tool-compat `rsvg` |
| Prepare `developer-qemu` | **OK** — Tree materialisiert |
| Controlled ISO Build | **BLOCKED** — Exit **30** `blocked_requires_operator_sudo_policy` |
| Neue ISO | **Nein** — altes Artefakt unverändert |

## Dependency-Preflight

| Tool | Status |
|------|--------|
| lb | `/usr/bin/lb` |
| xorriso | OK |
| mksquashfs | OK |
| grub-mkrescue | OK |
| isohybrid | OK |
| rsvg (host) | fehlt — **OK** via `build/rescue/tool-compat/bin/rsvg` im Build-PATH |
| rsvg-convert | `/usr/bin/rsvg-convert` (`librsvg2-bin`) |

## Prepare (erfolgreich)

```bash
export SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

`auto/config` `--bootappend-live` (Auszug):

```
console=tty0 console=ttyS0,115200n8 loglevel=7 systemd.log_level=debug systemd.show_status=true ignore_loglevel printk.devkmsg=on
```

- **kein** `quiet` / `splash` in `auto/config`
- Marker-Skripte im Tree: `SETUPHELFER_BOOT_MARKER_START`, Autopilot-, Agent-Marker

## Altes ISO (vor Build-Versuch)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 511705088 B (~488 MiB) |
| SHA256 | `6a44d1fe771299305408f9e74e7b0fa3a2e7f108a7bffb415f5f4f7f46d8baae` |
| mtime | 2026-06-01 ~07:54 |

## Build-Versuch

```bash
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu \
  --run-id rescue_developer_iso_20260601_serial_visibility
```

| Feld | Wert |
|------|------|
| `build_exit_code` / LB_EXIT | **30** |
| `error_code` | `blocked_requires_operator_sudo_policy` |
| `build_started` | **false** |
| `policy_is_tty` | false |
| `policy_sudo_noninteractive` | false |

**Zusätzlich (wenn Policy passiert):** Permission-Preflight würde `rescue_iso_build.permission_denied_dot_build` melden — `binary/`, `chroot/`, `cache/` root-owned vom Lauf 07:54. Operator-Clean mit sudo erforderlich.

## Operator-Folgekommandos (interaktives Terminal)

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
export SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu \
  --run-id rescue_developer_iso_20260601_serial_visibility
```

## QEMU-Smoke-Retry

**blocked** — kein neues ISO; Retry erst nach erfolgreichem Build + statischer ISO-Validierung.

## Guardrails

Kein QEMU, USB, Backup, Restore, apt, Push.
