# PI-RS-USB-MSI-FIX-001 — USB Update 1.10.0.14 und GE63 Boot Retest

Stand: 2026-07-12  
Sprint-ID: **PI-RS-USB-MSI-FIX-001**  
Ausgangscommit: `e37169d03f11d6d932a5a39f51584e974245d16d`

## Ausgangslage

| Feld | Wert |
|------|------|
| Payload vorher (Stick) | **1.10.0.13** (`3abb861a…`) |
| Payload nachher (SquashFS) | **1.10.0.14** (`665e44e4…`) |
| Fixes | Console-Shield, boot-progress tty1 Race, GUI/openvt Fallback (PI-RS-MSI-FIX-001) |
| Testgerät | MSI GE63 Raider RGB 8RF |

## Workspace-Hygiene

| Artefakt | Behandlung |
|----------|------------|
| `controlled_iso_build_latest_summary.json` | Gesichert unter `/home/volker/setuphelfer-backups/pi-rs-usb-msi-fix-001-hygiene-*`, per `git restore` zurückgesetzt |
| MSI-Retest-Evidence Session 2/3 | Tar-Backup im Hygiene-Ordner, **nicht gelöscht**, weiterhin untracked im Workspace |
| Code-Änderungen | Keine — nur untracked Evidence + neuer Sprint-Evidence-Ordner |

## Ziel-USB

| Feld | Wert |
|------|------|
| Device | `/dev/sda` |
| Modell | Intenso Ultra Line |
| Größe | 59G |
| SERIAL | 24111412110686 |
| TRAN | usb |
| Partitionen | `sda1` SETUPHELFER, `sda2` SETUP_LOGS |
| Root-Disk ausgeschlossen | **ja** (`/` = `/dev/nvme1n1p2`) |

## Payload 1.10.0.14

| Feld | Wert |
|------|------|
| Workspace-Artefakt | `build/rescue/filesystem.squashfs.repacked-1.10.0.14` |
| SHA256 | `665e44e40dfa5c384b85f4526d1a9dea6389a4ac60c9b1356e8530676a4c3ac7` |
| Vor-Write SHA (Stick) | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |

## USB-Write

| Feld | Wert |
|------|------|
| Script | `scripts/rescue-live/update-fat32-esp-live-payload.sh` |
| Modus | `--operator-confirm-update --execute-update` |
| Ergebnis | **`payload_update_status=success`** |
| Partition rewrite | nein |
| Vorbereitung | Partitionen unmounted (vorher `PARTITION_MOUNTED` blocker) |

## Verify

| Check | Ergebnis |
|-------|----------|
| `verify-fat32-esp-rescue-usb.sh` | **success** |
| SquashFS SHA256 auf Stick | **665e44e4…** ✓ |
| Secret-Dateien | absent |
| FAT32 ESP Layout | OK |

**Hinweis:** `setuphelfer/rescue/version.json` auf dem Stick zeigt weiterhin `project_version: 1.10.0.13` (Update-Script aktualisiert nur SquashFS + `payload_updated_at`). Inhaltliche Version ist über SquashFS-SHA und `/opt/setuphelfer-rescue/VERSION` im Live-System maßgeblich.

## MSI Boot-Retest

| Check | Ergebnis |
|-------|----------|
| Durchgeführt | **nein** — `operator_action_required` |
| Nächster Schritt | Stick am GE63 mit **MSI-Compat** GRUB booten |

### Operator-Checkliste (GE63)

1. MSI ausschalten, Stick einstecken
2. Boot-Menü → Setuphelfer **MSI-Compat** (`pci=noaer`, `setuphelfer_msi_compat=1`)
3. Beobachten:
   - TUI/Textmenü bleibt stehen (kein `ESC[2J` / „GUI übernimmt“)
   - `/run/setuphelfer/console-shield.json` mit `tty1_clear_allowed=false`
   - PCIe-AER ruhig (0 Zeilen erwartet)
   - GUI darf `startx_not_started` melden — TUI muss erhalten bleiben
4. SETUP_LOGS beschreiben lassen, Stick zurück ins Dev-System → Phase 13 Import

## Erwartete Ergebnisse (nach Boot)

| Bereich | Erwartung |
|---------|-----------|
| TUI-Stabilität | Textmenü bleibt sichtbar |
| Console-Shield | `console-shield.json` vorhanden, Journal nicht auf tty1 |
| boot-progress | Final *„Textmenü bereit“*, kein tty1-clear |
| GUI/openvt | optional fail, `tui_preserved=true` |
| Backend/API | `/api/version` HTTP 200 |

## Telemetry Preview

Nicht durchgeführt (kein Boot). Erwartung ohne Token: `blocked_missing_auth`, `real_send_executed=false`.

## SETUP_LOGS Import

Noch keine neuen Logs — Import nach GE63-Boot.

## Nicht durchgeführt

- Backup, Restore, Wipe
- produktiver Send / Lab Send
- DNS/IONOS/Plesk
- apt upgrade / Server-Reboot
- Repack (Artefakt vorhanden, SHA ok)

## Offene Risiken

- `version.json` auf FAT32 zeigt noch 1.10.0.13 als `project_version` (Metadaten-Drift)
- GUI unter MSI-Compat/nomodeset startet vermutlich weiterhin nicht
- Physischer Boot-Retest ausstehend

## Nächster Schritt

**Operator:** GE63 MSI-Compat-Boot mit Stick **1.10.0.14**, SETUP_LOGS importieren, Ergebnis in PI-RS-MSI-RETEST-003 oder Follow-up-Sprint dokumentieren.
