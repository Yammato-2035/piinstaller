# PI-RS-MSI-RETEST-002 Operator Boot Runbook

Stand: 2026-07-12
Sprint: Operator Boot Retest mit Payload **1.10.0.13**

## Entscheidung

Der Retest erfolgt mit dem vorhandenen physischen Stick/Payload:

| Feld | Wert |
|------|------|
| Stick/Payload-Version | **1.10.0.13** |
| Payload-SHA256 | `3abb861a9dfe8e6681912c5d19168f68607dc71bcf2de5b74ca589bd71e43b4c` |
| USB verify | success (PI-RS-USB-TELEMETRY-001) |
| Workspace-Version | **1.9.19.5** |
| Versionsdrift akzeptiert | **ja** (Operator-Entscheidung) |

## Nicht erlaubt

- Kein Repack
- Kein USB-Update (`dd`, `mkfs`, `parted`, `sgdisk`, `wipe`)
- Kein produktiver Telemetry Send (`preview_only=true`, `production_ready=false`)
- Keine Reparatur
- Kein Auto-Fix
- Kein Remote Command

## Testgerät

| Feld | Wert |
|------|------|
| Modell | MSI GE63 Raider RGB 8RF |
| Board | MS-16P5 |
| GPU | NVIDIA GTX 1070 + Intel iGPU |
| WLAN | Intel AC9560 |
| LAN | Killer E2500 |

## Vorbereitung (Entwicklungsrechner — erledigt)

- [x] Working Tree bereinigt (untracked `queue_preview_items` gesichert und entfernt)
- [x] Stick/Payload read-only bestätigt (`SETUPHELFER` ro, SHA256 match)
- [x] SETUP_LOGS Vorher-Snapshot dokumentiert
- [ ] Operator Boot Retest am MSI durchführen

## Boot-Test-Schritte (Operator am MSI)

**Wichtig (GE63):** Nicht den Default-Eintrag „sicherer Textmodus“ wählen — dort fehlen `pci=noaer` und MSI-Compat. Stattdessen:

**„Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus (Text)“** (Menüpunkt 5 in `grub.cfg`)

1. Stick am MSI einstecken.
2. MSI einschalten.
3. Boot-Menü öffnen (UEFI).
4. SETUPHELFER-Stick auswählen.
5. Bootmenü fotografieren.
6. Version/Payload-Hinweise fotografieren, falls sichtbar.
7. **TUI starten** (Text-Modus, `setuphelfer_mode=text`).
8. Prüfen:
   - TUI sichtbar
   - Tastatur reagiert
   - keine Bootschleife
   - keine Kernel-Panic
9. Backend/API prüfen, wenn UI/TUI entsprechende Funktion anbietet:
   - `/api/version` (127.0.0.1:8000)
   - Storage Discovery
   - Disk Inventory
10. **GUI starten**, falls Option vorhanden:
    - Erfolg / schwarzer Cursor / Fallback dokumentieren.
11. Netzwerk prüfen:
    - WLAN Intel AC9560 erkannt?
    - Killer E2500 Warnung?
12. Keine Reparatur starten.
13. Keine produktive Telemetry aktivieren.
14. **Telemetry Preview** (Shell, read-only):
    ```bash
    export SETUPHELFER_RS_TELEMETRY_ENDPOINT=https://telemetrie.setuphelfer.de/v1/telemetry/ingest
    export SETUPHELFER_RS_TELEMETRY_LAB_SEND_ENABLED=1
    export SETUPHELFER_RS_TELEMETRY_OPERATOR_APPROVAL=explicit
    export SETUPHELFER_RS_TELEMETRY_CONSENT_STATUS=granted_lab
    export SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE=/etc/setuphelfer/rescue/telemetry-lab-token
    /opt/setuphelfer-rescue/scripts/lab-rs-tel-send001-preview.sh
    ```
    Ohne Token: `blocked_missing_auth` dokumentieren. Mit Token: `dry_run_ready` erwarten.
15. **Optional ein Lab Send** nur wenn Preview `dry_run_ready`/`lab_send_ready`:
    `/opt/setuphelfer-rescue/scripts/lab-rs-tel-send001-send.sh`
16. Test beenden.
17. MSI herunterfahren.
18. Stick zurück an Entwicklungsrechner.
19. SETUP_LOGS sichern/importieren.

## Nach Rückkehr (Entwicklungsrechner)

1. `SETUP_LOGS` mounten
2. Import nach `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/imported-setup-logs/`
3. `docs/test-results/PI_RS_MSI_RETEST_002_GE63_RESULT.md` aktualisieren
4. Commit nur redacted/sichere Evidence

## Referenzen

- `docs/rescue-stick/PI_RS_MSI_RETEST_002_GE63_PAYLOAD_1_10_0_13.md` — Sprint-Doku
- `docs/test-plans/PI_RS_MSI_RETEST_001_GE63_RAIDER.md` — Checkliste
- `docs/evidence/pi_rs_msi_retest_002_ge63_payload_1_10_0_13/` — Evidence
