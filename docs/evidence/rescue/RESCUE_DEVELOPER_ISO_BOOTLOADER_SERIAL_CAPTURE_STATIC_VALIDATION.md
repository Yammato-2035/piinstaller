# Developer ISO — Bootloader Serial Capture Static Validation

**Stand:** 2026-06-01 (Post-Operator-Build)
**HEAD:** `a503e8e`
**Build-Run:** `rescue_developer_iso_20260601_bootloader_serial_capture`
**LB_EXIT:** 0

## ISO-Artefakt

| Feld | Wert |
|------|------|
| SHA256 | `5c79e35c35a227bdcb9978c1728d8d6aaeef515938ce13358ca6b994d293829a` |
| Vorherige SHA | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` |
| SHA geändert | **yes** |

## Tree-Befund (developer-qemu)

| Kriterium | Tree |
|-----------|------|
| ISOLINUX `SERIAL 0 115200` | **yes** |
| `TIMEOUT 30` | **yes** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **yes** |
| GRUB Serial vorgesehen | **yes** |
| `console=tty0` | **yes** |
| `console=ttyS0,115200n8` | **yes** |
| `quiet`/`splash` Developer-Append aktiv | **no** |
| Marker im Tree/chroot | **yes** |

## ISO-`strings`-Befund

| Kriterium | ISO |
|-----------|-----|
| ISOLINUX `SERIAL 0 115200` | **yes** |
| `TIMEOUT 30` | **yes** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **yes** |
| `console=tty0` | **yes** |
| `console=ttyS0` | **yes** |
| `loglevel=7` / `systemd.log_level=debug` | **yes** (in live-Append-Zeilen) |
| `quiet`/`splash` Developer-Boot-Append | **no** (live-`append`-Zeilen ohne quiet/splash; isolinux-`splash.png`/einzelnes `quiet` in anderen Menu-Kontexten) |
| Autopilot/Agent-Marker | **unknown** (Squashfs; Tree **yes**) |

## Bewertung

| Ampel | Bereich |
|-------|---------|
| **Grün** | Bootloader Serial/Autoboot + Cmdline tty0/ttyS0 im Tree und ISO |
| **Gelb** | Runtime-Marker erst nach QEMU-Boot sichtbar |

## QEMU-Smoke-Retry

**`ready_for_qemu_serial_smoke`**

## Abnahme

**Erfüllt:** Operator-Build Exit 0, SHA256 geändert, ISOLINUX-Serial/Timeout/Default im ISO, Developer-Cmdline mit tty0+ttyS0.
