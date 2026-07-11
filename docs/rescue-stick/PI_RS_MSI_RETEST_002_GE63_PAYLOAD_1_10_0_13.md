# PI-RS-MSI-RETEST-002 — GE63 Hardware-Test mit Rescue-Stick Payload 1.10.0.13

Stand: 2026-07-12
Sprint-ID: **PI-RS-MSI-RETEST-002**
Ausgangscommit: `6388e839653bf6cdd6152663985c9fe8a68e9b86`

## Ausgangslage

| Feld | Wert |
|------|------|
| Workspace | `/home/volker/piinstaller` |
| origin/main (Start) | `6388e839653bf6cdd6152663985c9fe8a68e9b86` |
| USB-Gerät | `/dev/sda` — Intenso Ultra Line 59G |
| Payload-Version (SETUPHELFER) | **1.10.0.13** |
| SquashFS SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |
| USB-Verify (PI-RS-USB-TELEMETRY-001) | success |
| Workspace-Projektversion | 1.9.19.5 (separater Track) |

## Testgerät

| Feld | Wert |
|------|------|
| Modell | MSI GE63 Raider RGB 8RF |
| Board | MS-16P5 |
| GPU | NVIDIA GTX 1070 + Intel iGPU |
| WLAN | Intel AC9560 |
| LAN | Killer E2500 |

## Sprint-Status

**`operator_action_required`**

Der physische Boot-Retest am MSI mit Payload **1.10.0.13** wurde in diesem Sprint **nicht** durchgeführt. Cursor/Agent kann Hardware-Boot nicht simulieren. Stick-Bereitschaft, Preflight und Operator-Runbook sind dokumentiert.

## USB Payload 1.10.0.13 — Dev-System-Verifikation

Read-only Mount von SETUPHELFER (2026-07-12):

- `setuphelfer/rescue/version.json` → `project_version=1.10.0.13`
- `live/filesystem.squashfs` SHA256 match
- `payload_updated_at`: 2026-07-11T21:59:29Z via `fat32_esp_payload_update_pi_rs_usb_telemetry_001`

Evidence: `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/stick-readiness-preflight.txt`

## Boot-Ergebnis (MSI — ausstehend)

| Check | Ergebnis |
|-------|----------|
| Boot erfolgreich | *ausstehend — Operator* |
| Schwarzer Bildschirm | *ausstehend* |
| TUI sichtbar | *ausstehend* |
| Fehlermeldung | *ausstehend* |

**Historischer Referenz-Boot (Payload 1.10.0.12, 2026-07-01):** SETUP_LOGS enthält erfolgreichen Boot auf GE63 (`boot-summary.json`, `api-endpoint-status.json`). Kein Boot-Nachweis für **1.10.0.13** auf SETUP_LOGS (0 Treffer für `1.10.0.13` / `msi-1.10.0.13-write-test.txt`).

## Versionserkennung

| Kontext | Version |
|---------|---------|
| Stick SETUPHELFER (read-only, Dev) | **1.10.0.13** ✓ |
| SETUP_LOGS api-version.json (letzter MSI-Lauf) | 1.10.0.12 (historisch) |
| Erwartung nach MSI-Boot | 1.10.0.13 |

## TUI / GUI / API

| Check | Ergebnis |
|-------|----------|
| TUI startet | *ausstehend* |
| GUI getestet | *ausstehend* |
| Backend/API HTTP 200 | *ausstehend* (Referenz 1.10.0.12: rescue-health, disk-inventory, storage-discovery → 200) |

## SETUP_LOGS Schreibbarkeit

| Check | Ergebnis |
|-------|----------|
| SETUP_LOGS gemountet | *ausstehend am MSI* |
| Schreibtest `msi-1.10.0.13-write-test.txt` | *ausstehend* |

## Hardware-Erkennung

| Check | Ergebnis |
|-------|----------|
| Laufwerke erkannt | *ausstehend* (Referenz: `lsblk.json` aus RS-011B) |
| WLAN/LAN erkannt | *ausstehend* |
| PCIe/AER Hinweise | *ausstehend* |
| Kritische Fehler | *ausstehend* |

Nur Diagnose/Read-only — kein Backup, Restore oder Wipe.

## Telemetry Preview

| Check | Ergebnis |
|-------|----------|
| Preview durchgeführt (gebooteter Stick) | **nein** |
| Erwartung ohne Token auf Live-System | `blocked_missing_auth` |
| Erwartung mit Token + Gates | `send_status=dry_run_ready`, `health_ok`, `auth_present=true`, `real_send_executed=false` |

Token ist **nicht** im Payload (`/etc/setuphelfer/rescue/telemetry-lab-token` fehlt auf Standard-Stick). Preview/Send-Scripts sind in SquashFS **1.10.0.13** enthalten.

Referenz Lab Send (Dev-System, PI-RS-TEL-SEND-001): `req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca` — **nicht** von diesem MSI-Retest.

## Optionaler Lab Send

| Check | Ergebnis |
|-------|----------|
| Lab Send vom gebooteten Stick | **nein** (Preview nicht durchgeführt) |

Nur erlaubt wenn Preview `dry_run_ready` oder `lab_send_ready` meldet und Token + Consent + `operator_approval=explicit` vorhanden.

## Ingest Acceptance

Baseline vom Telemetry-Server (2026-07-12, kein neuer MSI-Send):

| Feld | Wert |
|------|------|
| request_id (letzter rescue_stick Event) | `req-fd36496e-e1f8-41c7-9cba-9dfb735ff1ca` |
| source | rescue_stick |
| accepted | true |
| raw_payload_visible | false |
| MSI-Retest request_id | *nicht vorhanden* |

Evidence: `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/telemetry-ingest-status-redacted.txt`

## Import SETUP_LOGS

| Feld | Wert |
|------|------|
| SETUP_LOGS auf Stick gefunden | ja (read-only Mount) |
| Post-Retest-Import | nein — nur historische Baseline (5 Dateien) |
| Secret-Check | bestanden (harmlose Feldnamen `token_source_present`) |

Import-Pfad: `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/imported-setup-logs/`

## Tests / Gates

| Gate | Ergebnis |
|------|----------|
| pytest `test_pi_rs_tel_send001_*` + `test_pi_rs_payload_telemetry001_*` | 28/28 passed |
| `check-rescue-payload-no-secrets.sh` | passed |

## Nicht durchgeführt

- Backup, Restore, Wipe
- Schreibaktionen auf interne MSI-Datenträger
- Produktiver Telemetry Send
- Lab Send vom gebooteten Stick
- USB-Schreiben / Repack
- DNS/IONOS/Plesk-Änderungen
- apt upgrade / Server-Reboot

## Offene Risiken

1. **Kein Boot-Smoke mit 1.10.0.13** — SquashFS-Inhalt (Telemetry-Scripts) noch nicht auf GE63-Hardware verifiziert.
2. **TLS auf Cloud-Endpoint** — `telemetrie.setuphelfer.de` weiterhin TLS-Probleme (TEL-CLOUD-FIX-001); Lab-Ingest über Server-Health OK.
3. **Token nicht im Payload** — Telemetry Preview am Stick erwartet `blocked_missing_auth` bis Operator Token bereitstellt.

## Nächster Schritt

1. Operator: MSI booten gemäß `docs/test-plans/PI_RS_MSI_RETEST_002_OPERATOR_BOOT_RUNBOOK.md` (aktualisiert auf **1.10.0.13**).
2. SETUP_LOGS importieren → `imported-setup-logs/` aktualisieren.
3. Telemetry Preview am gebooteten Stick; optional ein Lab Send wenn Gates grün.
4. Ergebnis in `docs/test-results/PI_RS_MSI_RETEST_002_GE63_RESULT.md` abschließen.

## Evidence

`docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/`
