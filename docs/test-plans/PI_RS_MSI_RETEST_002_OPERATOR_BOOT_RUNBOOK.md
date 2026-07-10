# PI-RS-MSI-RETEST-002 Operator Boot Runbook

Stand: 2026-07-10
Sprint: Operator Boot Retest mit Payload **1.10.0.12**

## Entscheidung

Der Retest erfolgt mit dem vorhandenen physischen Stick/Payload:

| Feld | Wert |
|------|------|
| Stick/Payload-Version | **1.10.0.12** |
| Payload-SHA256 | `1a72046a40a504e62771a8fc8cd4b6360951c3ac0a4e352a8248fc68f14487e6` |
| Workspace-Version | **1.9.19.4** |
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
14. Test beenden.
15. MSI herunterfahren.
16. Stick zurück an Entwicklungsrechner.
17. SETUP_LOGS sichern/importieren gemäß `PI_RS_MSI_RETEST_001_IMPORT_AND_REVIEW.md`.

## Nach Rückkehr (Entwicklungsrechner)

1. `SETUP_LOGS` mounten
2. Phase 8 Import ausführen (`docs/evidence/rescue/imports/pi-rs-msi-retest-002-ge63-*`)
3. `docs/test-results/PI_RS_MSI_RETEST_002_GE63_RESULT.md` aktualisieren
4. Commit nur redacted/sichere Evidence

## Referenzen

- `docs/test-plans/PI_RS_MSI_RETEST_001_GE63_RAIDER.md` — Checkliste
- `docs/test-plans/PI_RS_MSI_RETEST_001_OPERATOR_RUNBOOK.md` — Vorbereitung
- `docs/evidence/pi_rs_msi_retest_002_ge63_operator_boot_retest/` — Preflight-Evidence
