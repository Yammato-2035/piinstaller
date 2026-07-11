# PI-RS-TEL-SEND-001 — Rescue-Stick Lab Send gegen Cloud-Ingest

**Status:** `lab_send_accepted`
**Datum:** 2026-07-11
**Workspace:** `/home/volker/piinstaller`

## Ausgangslage

- **TEL-CSE-AUTH-001** abgeschlossen — CSE Lab Send accepted (`req-e9654932-ecdb-48cb-85da-277a334902b3`)
- Cloud-Ingest bestätigt: `https://telemetrie.setuphelfer.de/v1/telemetry/ingest`
- Telemetry Server `0.2.0-beta` unter `/opt/setuphelfer-telemetry` (IONOS `85.215.118.240`)

## Ziel-Endpunkt

```
https://telemetrie.setuphelfer.de/v1/telemetry/ingest
```

## Rescue-Stick Auth-Client

| Feld | Wert |
|------|------|
| `client_id` | `rescue_stick_lab` |
| `source` | `rescue_stick` |
| Token-Datei (Server) | `/etc/setuphelfer/rescue/telemetry-lab-token` (600, root:root, 44 bytes) |
| Token-Datei (Dev-Lab) | `/home/volker/.config/setuphelfer/rescue/telemetry-lab-token` (600, lokal) |
| Env | `SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE` |

Token via Telemetry-Server Export-CLI erzeugt — **Secret nie im Git, nie in Evidence**.

## Gates (alle Pflicht)

| Gate | Wert |
|------|------|
| `health_prerequisite` | `health_ok` |
| `consent_status` | `granted_lab` |
| `operator_approval` | `explicit` |
| `lab_send_enabled` | `1` / `true` |
| `auth_present` | `true` |

## Payload (`rs.telemetry.lab.v1`)

- `source=rescue_stick`
- `environment=lab`
- `production_ready=false`
- `contains_pii=false`
- `raw_logs_visible=false`
- `payload_hash` vorhanden (sha256)
- Keine PII, keine Rohlogs, keine Secrets

Implementierung: `backend/core/rescue_stick_cloud_lab_{models,config,payload,send}.py`

## Preview

Script: `scripts/lab-rs-tel-send001-preview.sh`

Ergebnis: `send_status=dry_run_ready`, `real_send_executed=false`

Evidence: `docs/evidence/pi_rs_tel_send_001_rescue_stick_lab_send/rs-send-preview-redacted.txt`

## Lab Send (einmalig)

Script: `scripts/lab-rs-tel-send001-send.sh`

| Feld | Wert |
|------|------|
| Status | `lab_send_accepted` |
| HTTP | 200 |
| `request_id` | `req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca` |
| Classification | `lab_send_accepted` |

Evidence: `docs/evidence/pi_rs_tel_send_001_rescue_stick_lab_send/rs-lab-send-redacted.txt`

## Ingest Acceptance

Lab-Status-API auf Server:

- `GET /v1/telemetry/lab/status` — last event `source=rescue_stick`, `accepted=true`
- `GET /v1/telemetry/lab/events/recent` — `request_id` wiederfindbar
- `raw_payload_visible=false`

Evidence: `docs/evidence/pi_rs_tel_send_001_rescue_stick_lab_send/ingest-acceptance-redacted.txt`

## Telemetry-Server-Erweiterung (Server-Deploy, kein DNS)

Für `rs.telemetry.lab.v1` / `source=rescue_stick`:

- `app/services/rs_lab_ingest.py`
- `validate_rs_lab_payload_bytes` in `payload_validator.py`
- Env: `TS_RS_LAB_BEARER_ENABLED=1`, `TS_RS_LAB_BEARER_TOKEN_FILE`, `TS_RS_LAB_CLIENT_ID=rescue_stick_lab`

Deploy nach `/opt/setuphelfer-telemetry` — **nicht** im piinstaller-Repo (private telemetry-server).

## Wiederverwendung bestehender Struktur

| Bereich | Aktion |
|---------|--------|
| PI-RS-TEL-001/002 HMAC Lab Flow | **Nicht dupliziert** — separater Cloud-Bearer-Pfad |
| PI-RS-TEL-004 Endpoint/Health | **Wiederverwendet** (Cloud-URL, Health-Check) |
| Neuer Code | `rescue_stick_cloud_lab_*` + Preview/Send-Scripts + 6 Testdateien |

## Nicht durchgeführt

- Produktiver Send
- Repack / USB-Schreiben / ISO-SquashFS-Build
- DNS / IONOS / Plesk-Änderungen
- `apt upgrade` / Reboot
- Secrets im Git

## Risiken

- Physischer Stick noch **1.10.0.12** — Lab Send aus Workspace, nicht vom Stick-Boot
- Öffentliches DNS für `telemetrie.setuphelfer.de` kann von Plesk-intern abweichen (TLS-Historie)
- RS-Lab-Ingest Server-Code liegt im **private** telemetry-server Repo — piinstaller allein reicht nicht für Acceptance

## Nächster Schritt

Bei `lab_send_accepted` (erreicht):

**PI-RS-PAYLOAD-TELEMETRY-001** — Repack mit bestätigtem Rescue-Stick Lab Send

Offen wartend:

**CSE-OPS-MAINT-001** — Server Updates + kontrollierter Reboot + Post-Reboot-Smoke
