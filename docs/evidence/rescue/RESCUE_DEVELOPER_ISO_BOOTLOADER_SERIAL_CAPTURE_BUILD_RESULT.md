# Developer Rescue ISO — Bootloader Serial Capture Rebuild

**Stand:** 2026-06-01 (Operator-Terminal-Build)
**HEAD:** `a503e8e` (Doku vor Build); Build auf gleichem Stand
**Branch:** `main`
**Repository:** PUBLIC (`Yammato-2035/piinstaller`)
**Push allowed:** no
**Push durchgeführt:** no
**NDA risk:** blocked (public repository)

## Zusammenfassung

| Phase | Ergebnis |
|-------|----------|
| Profil-Gate vor Build | **OK** — `install_profile=release`, Exit 0 |
| Clean (`--operator-confirm-clean`) | **yes** — Operator-Terminal mit sudo |
| Prepare `developer-qemu` | **yes** — Exit 0 |
| Controlled ISO Build | **OK** — `LB_EXIT=0`, `status=success` |
| Neue ISO | **yes** — SHA geändert |
| QEMU-Smoke-Retry | **`ready_for_qemu_serial_smoke`** |

## Operator-Build

| Feld | Wert |
|------|------|
| Run-ID | `rescue_developer_iso_20260601_bootloader_serial_capture` |
| Gestartet | 2026-06-01T21:55:36+02:00 |
| Beendet | 2026-06-01T21:59:21+02:00 |
| `exit_code` / LB_EXIT | **0** |
| `execution_mode` | `manual_operator_terminal` |
| `policy_guard_status` | ready |
| `build_started` | true |
| `error_code` | null |

Vorheriger Blockiert-Lauf (Agent): Exit **30** / **34** — durch Operator-Clean+Build ersetzt.

## ISO-Artefakt

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 511705088 B (~488 MiB) |
| mtime | 2026-06-01 21:59:19 |
| **old_iso_sha256** | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` |
| **new_iso_sha256** | `5c79e35c35a227bdcb9978c1728d8d6aaeef515938ce13358ca6b994d293829a` |
| **new_iso_differs_from_old** | **yes** |

## Prepare-Tree (developer-qemu)

| Prüfung | Tree |
|---------|------|
| ISOLINUX `SERIAL 0 115200` | **yes** |
| `TIMEOUT 30` | **yes** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **yes** |
| GRUB Serial-Hook | **yes** |
| `console=tty0` / `ttyS0` | **yes** |
| `quiet`/`splash` im Developer-Append | **no** |
| Marker-Skripte im Tree/chroot | **yes** (`setuphelfer-qemu-smoke-autopilot.sh`, `setuphelfer-serial-boot-markers.sh`) |

## Guardrails

Kein QEMU-Lauf, kein USB/dd, kein Backup/Restore, kein apt, kein Push, keine Build-Artefakte in Git.

## Nächster Schritt

`QEMU_DEVELOPER_SERIAL_SMOKE_RETRY_AFTER_BOOTLOADER_FIX`
