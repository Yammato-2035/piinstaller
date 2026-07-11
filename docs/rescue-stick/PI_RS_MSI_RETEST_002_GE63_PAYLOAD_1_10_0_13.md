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

**`partial_fail`** — MSI-Boot mit **1.10.0.13** durchgeführt (Session `20260712_002439`); TUI durch PCIe-AER-Flut nahezu unbrauchbar; GUI-Start fehlgeschlagen.

## Boot-Ergebnis (MSI — 2026-07-12)

| Check | Ergebnis |
|-------|----------|
| Boot erfolgreich | **ja** |
| Schwarzer Bildschirm | **nein** |
| TUI sichtbar | **ja, nahezu unbrauchbar** (PCIe-AER-Flut) |
| Fehlermeldung | GUI: `startx_not_started`; openvt VT2-Fehler |
| GRUB-Eintrag | Default Textmodus **ohne** `pci=noaer` |

## Versionserkennung

| Kontext | Version |
|---------|---------|
| Stick SETUPHELFER | **1.10.0.13** ✓ |
| Boot-Session SETUP_LOGS | `20260712_002439` auf GE63 |

## TUI / GUI / API

| Check | Ergebnis |
|-------|----------|
| TUI startet | **ja** (Textmodus) |
| GUI getestet | **ja — fehlgeschlagen** |
| Backend/API HTTP 200 | *nicht verifiziert* (disk-discovery TypeError) |

## SETUP_LOGS Schreibbarkeit

| Check | Ergebnis |
|-------|----------|
| SETUP_LOGS gemountet | **ja** |
| Diagnostics persistiert | **ja** (`20260712_002439_boot`) |
| Schreibtest `msi-1.10.0.13-write-test.txt` | **nein** (nicht angelegt) |

## Hardware-Erkennung

| Check | Ergebnis |
|-------|----------|
| Laufwerke erkannt | *teilweise* (disk-discovery Exception TypeError) |
| WLAN/LAN erkannt | **ja** (iwlwifi, Killer E2500/alx) |
| PCIe/AER Hinweise | **ja — ~428 Zeilen**, Killer E2500 @ 05:00.0 |
| Kritische Fehler | **nein** (nur Corrected AER) |

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

1. **Default-GRUB ohne MSI-Compat** — PCIe-AER-Flut zerstört TUI-Konsole; separater Menüpunkt existiert, ist aber nicht Default.
2. **GUI-Start scheitert** — `startx_not_started`, openvt kann VT2 nicht freigeben (evtl. PCIe/Konsolen-Konflikt).
3. **disk-discovery TypeError** auf 1.10.0.13 — Backend-Diagnose eingeschränkt.
4. **TLS auf Cloud-Endpoint** — weiterhin problematisch (TEL-CLOUD-FIX-001).

## Nächster Schritt

1. **Erneut booten** mit GRUB-Menüpunkt **„Setuphelfer MSI/NVIDIA Kompatibilitätsmodus (Text)“** (enthält `pci=noaer`).
2. TUI-Bedienbarkeit prüfen; GUI optional erneut testen.
3. GRUB-Default auf Stick anpassen (Fix-Sprint, kein USB-Write ohne Freigabe).

## Evidence

`docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/`
