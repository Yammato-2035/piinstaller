# QEMU Guest Agent Smoke — Serial Review After Preflight

**Datum:** 2026-06-03  
**Run:** `qemu_rescue_developer_autopilot_20260602_202725` (pre-fix, siehe Run Identification)

## Log-Größen

| Log | Bytes |
|-----|-------|
| qemu-serial.log | **0** |
| qemu-gtk-stdout.log | **0** |
| qemu-gtk-stderr.log | **71** |

## Pflichtbewertung

| Marker | Gesehen |
|--------|---------|
| serial_size_bytes | **0** |
| bootloader_seen | **no** |
| kernel_seen | **no** |
| initrd_seen | **no** |
| systemd_seen | **no** |
| live_system_seen | **no** |
| login_seen | **no** |
| setuphelfer_runtime_seen | **no** |
| autopilot_seen | **no** |
| devserver_contact_seen | **no** |
| panic_seen | **no** |
| fatal_error_seen | **no** (nur leere/minimale stderr) |

**Status:** `blocked` — `qemu_serial_capture_failure` auf Standard-ISO ohne `console=ttyS0` (bekannter Vor-Fix-Lauf).

Post-ISO-Rebuild-Serial **nicht** bewertbar — kein neuer Smoke-Log vorhanden.
