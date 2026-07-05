> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/DEV_CONTROL_CENTER_FLEET_SESSIONS_EN.md`). Bitte bei Release manuell gegenlesen.

# Lab Sessions (Fleet Session Phase 1)

## Purpose

The **Lab Sessions** tile in the Centre de contrôle du développement (**Telemetry** tab) shows **host-side** QEMU/lab smoke runs as soon as the wrapper starts — **without** waiting for a guest Development Server report.

## vs Development Server

| Lab Sessions | Development Server |
|--------------|-------------------|
| Host wrapper run | Ingested guest Nondes |
| Visible immediately on start | After report/registry |
| Non SSH/remote actions | Optional lecture seule SSH |

## LED semantics

- **Grey:** Non session / Inconnu
- **Blue pulsing:** running smoke, fresh heartbeat
- **jaune:** `serial_empty`, `guest_report_missing`, delayed heartbeat
- **rouge:** `timeout`, `failed`, QEMU Erreur
- **vert:** `Succès` with guest report

## Typical findings

- `qemu_timeout_124` — QEMU killed by `timeout` (exit 124)
- `serial_empty` — `qemu-serial.log` stays 0 bytes
- `guest_report_missing` — `dev_server_report_new=false`

## Enablement

- `SETUPHELFER_FLEET_SESSIONS_ENABLED=true` or dev mode (`PI_INSTALLER_DEV=1`)
- Retourend must expose fleet routes (after runtime Déploiement/restart)

## Out of scope

Non school/production fleet, Non wake/remote start, Non E2E consent (roadmap phase 4).
