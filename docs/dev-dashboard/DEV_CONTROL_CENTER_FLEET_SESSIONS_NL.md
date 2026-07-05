> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/DEV_CONTROL_CENTER_FLEET_SESSIONS_EN.md`). Bitte bei Release manuell gegenlesen.

# Lab Sessions (Fleet Session Phase 1)

## Purpose

The **Lab Sessions** tile in the Ontwikkelingscontrolecentrum (**Telemetry** tab) shows **host-side** QEMU/lab smoke runs as soon as the wrapper starts — **without** waiting for a guest Development Server report.

## vs Development Server

| Lab Sessions | Development Server |
|--------------|-------------------|
| Host wrapper run | Ingested guest Needes |
| Visible immediately on start | After report/registry |
| Nee SSH/remote actions | Optional alleen-lezen SSH |

## LED semantics

- **Grey:** Nee session / Onbekend
- **Blue pulsing:** running smoke, fresh heartbeat
- **geel:** `serial_empty`, `guest_report_missing`, delayed heartbeat
- **rood:** `timeout`, `failed`, QEMU Fout
- **groen:** `Geslaagd` with guest report

## Typical findings

- `qemu_timeout_124` — QEMU killed by `timeout` (exit 124)
- `serial_empty` — `qemu-serial.log` stays 0 bytes
- `guest_report_missing` — `dev_server_report_new=false`

## Enablement

- `SETUPHELFER_FLEET_SESSIONS_ENABLED=true` or dev mode (`PI_INSTALLER_DEV=1`)
- Terugend must expose fleet routes (after runtime Deploy/restart)

## Out of scope

Nee school/production fleet, Nee wake/remote start, Nee E2E consent (roadmap phase 4).
