# QEMU Guest Agent — Serial Review

**Run-ID:** `qemu_rescue_developer_autopilot_20260602_202725`  
**Serial:** `qemu-serial.log`

## Größen

| Log | Bytes |
|-----|-------|
| qemu-serial.log | **0** |
| qemu-gtk-stdout.log | **0** |
| qemu-gtk-stderr.log | **71** (`terminating on signal 15 from pid … (timeout)`) |

## Marker

| Marker | Gesehen |
|--------|---------|
| bootloader_seen | **no** |
| kernel_seen | **no** |
| initrd_seen | **no** |
| systemd_seen | **no** |
| live_system_seen | **no** |
| login_seen | **no** |
| setuphelfer_runtime_seen | **no** |
| dev_agent_marker_seen | **no** |
| panic_seen | **no** |
| fatal_error_seen | **no** (nur Host-Timeout) |

## ISO-Bootappend (Standard-Profil)

`auto/config` / `isolinux/live.cfg`:
```
… init=/lib/systemd/systemd quiet splash setuphelfer_rescue=1 …
```

**Kein** `console=ttyS0` — im Gegensatz zum `developer-qemu`-Profil (Prior erfolgreicher Serial-Smoke: 132412 B mit `console=ttyS0,115200n8`).

## Status

**serial_empty** — Bootzustand im Gast **nicht belegbar** über Serial.

Vergleich: `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` (developer-qemu + ttyS0 → ISOLINUX/systemd sichtbar).

## Serial-Status-Klassifikation

**serial_empty** (nicht `boot_reached_systemd` — keine Evidenz)
