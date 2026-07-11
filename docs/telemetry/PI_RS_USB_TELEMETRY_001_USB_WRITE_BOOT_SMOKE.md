# PI-RS-USB-TELEMETRY-001 — USB Write + Boot Smoke

**Status:** `usb_write_complete` / `boot_smoke_operator_action_required`  
**Datum:** 2026-07-11

## Ausgangslage

- Payload **1.10.0.13** lokal repacked (PI-RS-PAYLOAD-TELEMETRY-001)
- Physischer Stick zuvor **1.10.0.12** / ältere SquashFS-Hashes
- PI-RS-TEL-SEND-001 Lab Send accepted: `req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca`

## Ziel-USB

| Feld | Wert |
|------|------|
| Device | `/dev/sda` |
| Größe | 59G |
| Modell | Intenso Ultra Line |
| SERIAL | 24111412110686 |
| TRAN | usb |
| Partitionen | SETUPHELFER (sda1), SETUP_LOGS (sda2) |
| Root-Disk ausgeschlossen | ja (`/` = `/dev/nvme1n1p2`) |

## Payload-Artefakt

| Feld | Wert |
|------|------|
| Version | 1.10.0.13 |
| Pfad | `build/rescue/filesystem.squashfs.repacked-1.10.0.13` |
| SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |

## Schreibmethode

Script: `scripts/rescue-live/update-fat32-esp-live-payload.sh`

- Modus: FAT32 ESP live payload update (nur SquashFS, keine Partition-Neuformatierung)
- Confirm phrase: `UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD`
- Ergebnis: `payload_update_executed=true`, `verify_status=success`
- Runtime evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260711_215557`

Alte SquashFS auf Stick: `7bba91a0cff458025a0dc64f9dc12dff4cd3b637a9b57131cf7ddfb523ae191d`

## Verify (read-only)

`verify-fat32-esp-rescue-usb.sh --expected-squashfs-sha256 3abb861a…` — **OK**

Stick-Metadaten nach Write:

- `setuphelfer/rescue/version.json` → `project_version=1.10.0.13`
- SquashFS intern: `opt/setuphelfer-rescue/VERSION` → `1.10.0.13`
- Lab-Module + Scripts im SquashFS vorhanden

## Boot-Smoke

**Nicht in diesem Sprint ausgeführt** — physischer Boot erfordert Operator.

Siehe: `docs/evidence/pi_rs_usb_telemetry_001_usb_write_boot_smoke/boot-smoke-operator-required.txt`

## Telemetry Preview / Send vom Stick

Nicht ausgeführt (kein Boot). Erwartung nach Boot ohne Token-Provisionierung: `blocked_missing_auth`.

## Ingest Acceptance

Kein neuer Stick-Boot-Send in diesem Sprint. Letzter bestätigter Rescue-Send weiterhin Dev-Workspace `req-fd36496e-…`.

## Nicht durchgeführt

- Physischer Boot-Smoke
- Lab Send vom gebooteten Stick
- Backup / Restore / Wipe
- DNS/IONOS/Plesk
- apt upgrade / Server-Reboot

## Risiken

- Boot-Verhalten erst nach Hardware-Retest verifizierbar
- Lab-Token nicht im Payload — Auth auf Live-System separat nötig
- `version.json` git_commit-Feld noch historisch (Metadaten, kein Secret)

## Nächster Schritt

1. **Operator Boot Smoke** vom Stick (Checkliste in Evidence)
2. **PI-RS-MSI-RETEST-002** mit Payload 1.10.0.13
3. Optional: **CSE-OPS-MAINT-001**
