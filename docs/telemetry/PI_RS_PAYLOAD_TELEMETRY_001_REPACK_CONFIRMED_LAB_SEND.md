# PI-RS-PAYLOAD-TELEMETRY-001 — Repack mit bestätigtem Rescue-Stick Lab Send

**Status:** `repack_complete`
**Datum:** 2026-07-11
**Repo:** `/home/volker/piinstaller` @ PI-RS-TEL-SEND-001 merge

## Ausgangslage

- **PI-RS-TEL-SEND-001** accepted: `req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca`, `source=rescue_stick`
- Physischer Stick/Payload vorher: **1.10.0.12**
- CSE Lab Send (Referenz): `req-e9654932-ecdb-48cb-85da-277a334902b3`

## Ziel

Payload **1.10.0.13** enthält den bestätigten Lab-Send-Code aus PI-RS-TEL-SEND-001.

## Version

| Feld | Wert |
|------|------|
| Vorher | `1.10.0.12` |
| Nachher | `1.10.0.13` |
| Source of Truth | `config/rescue_payload_version.json` |
| Runtime-Helper | `backend/core/rescue_payload_version.py` |

## Enthalten im SquashFS

- `backend/core/rescue_stick_cloud_lab_{models,config,payload,send}.py`
- `scripts/lab-rs-tel-send001-preview.sh`
- `scripts/lab-rs-tel-send001-send.sh`
- `config/rescue_payload_version.json`
- `config/rescue_telemetry_endpoints.json`

## Nicht enthalten

- `telemetry-lab-token` / `telemetry-lab-hmac-key`
- `.env` / Secrets / Raw Evidence
- Authorization Header / API Keys

## Sicherheit

- `production_ready=false`
- Lab-only, consent + operator approval + `lab_send_enabled` erforderlich
- Kein produktiver Send default

## Repack

| Feld | Wert |
|------|------|
| Script | `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh` |
| Quelle | `build/rescue/filesystem.squashfs.repacked-1.10.0.12` |
| Modus | SquashFS repack only (kein lb, kein USB) |

## Payload-Artefakt

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/filesystem.squashfs.repacked-1.10.0.13` |
| Größe | ~1,2 GB |
| SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |

## Checks

- `scripts/check-rescue-payload-telemetry-content.sh` — **content_ok: true**
- `scripts/check-rescue-payload-no-secrets.sh` — **passed**
- Lab Preview (Workspace): **dry_run_ready**, `health_ok`

## Nicht durchgeführt

- USB-Schreiben
- Produktiver Send
- DNS/IONOS/Plesk-Änderungen
- apt upgrade / Reboot

## Nächster Schritt

**PI-RS-USB-TELEMETRY-001** — USB Write + Boot Smoke mit Payload 1.10.0.13

Alternativ: **CSE-OPS-MAINT-001** Server Update/Reboot
