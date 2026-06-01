# IST-Analyse — Rescue ISO Serial / Boot Visibility

**Stand:** 2026-06-01 · **Kontext:** QEMU-Smoke `081222`, Klasse `serial_empty_boot_unknown`

## Kernel-Cmdline-Quellen

| Quelle | Rolle |
|--------|--------|
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | Setzt `LIVE_BOOTAPPEND` und schreibt `auto/config` (`--bootappend-live`) |
| `build/rescue/live-build/setuphelfer-rescue-live/auto/config` | live-build lb config (generiert; **kann veraltet sein**) |
| `config/bootloaders/isolinux/*` | Templates von live-build; Append kommt aus `--bootappend-live` |
| Hybrid ISO | ISOLINUX + GRUB-Einträge aus gleichem Append |

## Befund Lauf 081222 / bestehende ISO

- Host-`qemu-serial.log`: **0 Bytes** nach 1200s.
- `strings` auf `binary.hybrid.iso`: `console=ttyS0,115200n8` **und** `quiet splash` — **ohne** `console=tty0`, ohne `loglevel=7`.
- Workspace-`auto/config` (Stand Analyse): `--bootappend-live "… console=ttyS0,115200n8 quiet splash …"` — **nicht** Developer-QEMU-SOLL.

**Schluss:** ISO vom 01.06. wurde sehr wahrscheinlich **nicht** mit `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu` + aktuellem Prepare-Stand gebaut, oder Tree/ISO divergiert.

## Developer-QEMU-Profil (Source)

| Artefakt | Vorhanden |
|----------|-----------|
| `build/rescue/profiles/developer-qemu/` | ja |
| `setuphelfer-qemu-smoke-autopilot.sh` + `.service` | ja, `TTYPath=/dev/ttyS0` |
| `setuphelfer-serial-boot-markers.sh` + `.service` | ja (früher Boot-Marker) |
| Hook `090-enable-qemu-smoke-autopilot.hook.chroot` | enable beider Units |

## console=ttyS0 / tty0 / quiet / splash

| Parameter | Prepare `developer-qemu` (SOLL nach Fix) | Standard-Profil | Alte ISO / alter Tree |
|-----------|------------------------------------------|-----------------|------------------------|
| `console=tty0` | ja | nein | oft nein |
| `console=ttyS0,115200n8` | ja | nein | ja |
| `quiet splash` | **nein** | ja | **ja** (Problem) |
| `loglevel=7` / systemd debug | ja | nein | nein |

## Autopilot / Serial

- Autopilot loggt per `log_serial` → `/dev/ttyS0` + `logger`.
- Erwartete Marker: `SETUPHELFER_BOOT_MARKER_START`, `SETUPHELFER_SYSTEMD_MARKER_START`, `SETUPHELFER_AUTOPILOT_START`, Devserver-Agent-Marker.
- Ohne Boot/Serial am Host sind diese im Lauf 081222 **nicht** nachweisbar.

## Secrets

- Marker enthalten nur Run-ID und feste Lab-URL `http://10.0.2.2:8001` — keine Tokens.

## Lücke Fleet-Finish (081222)

- Evidence-Datei `qemu-serial.log` existierte, Fleet `serial.path=""`, `exists=false`.
- `qemu.exit_code` null in API, obwohl Autopilot `124` dokumentierte.
- `kvm_enabled=false` trotz KVM im Wrapper.
