# Lab Sessions (Fleet Session Phase 1)

## Purpose

The **Lab Sessions** tile in the Development Control Center (**Telemetry** tab) shows **host-side** QEMU/lab smoke runs as soon as the wrapper starts — **without** waiting for a guest Development Server report.

## vs Development Server

| Lab Sessions | Development Server |
|--------------|-------------------|
| Host wrapper run | Ingested guest nodes |
| Visible immediately on start | After report/registry |
| No SSH/remote actions | Optional read-only SSH |

## LED semantics

- **Grey:** no session / unknown
- **Blue pulsing:** running smoke, fresh heartbeat
- **Yellow:** `serial_empty`, `guest_report_missing`, delayed heartbeat
- **Red:** `timeout`, `failed`, QEMU error
- **Green:** `success` with guest report

## Typical findings

- `qemu_timeout_124` — QEMU killed by `timeout` (exit 124)
- `serial_empty` — `qemu-serial.log` stays 0 bytes
- `guest_report_missing` — `dev_server_report_new=false`

## Enablement

- `SETUPHELFER_FLEET_SESSIONS_ENABLED=true` or dev mode (`PI_INSTALLER_DEV=1`)
- Backend must expose fleet routes (after runtime deploy/restart)

## Out of scope

No school/production fleet, no wake/remote start, no E2E consent (roadmap phase 4).
