# R.5C — Test Matrix Evaluation

**Datum:** 2026-06-13  
**Datenquelle:** Stick-Mount — **keine** `matrix/rescue_test_matrix_latest.*` vorhanden

## Tabelle

| Bereich | Status | Evidence | Blocker | Nächste Aktion |
|---------|--------|----------|---------|----------------|
| Boot | **red** | fehlt | Kein Live-Boot nachgewiesen | MSI-Boot wiederholen / R.6-Bootfix |
| GRUB | **yellow** | `grub.cfg` static OK, Theme staged | Kein Runtime-GRUB-Log | MSI Boot beobachten |
| Stick-Persistenz | **red** | `/setuphelfer-evidence/` fehlt | Boot oder Mount-Erkennung | R.6-Persistencefix |
| TUI | **unknown** | fehlt | — | Nach Boot prüfen |
| grafisches Menü | **unknown** | fehlt | — | Nach Boot prüfen |
| Browser | **unknown** | fehlt | — | Nach Boot prüfen |
| Kiosk | **unknown** | fehlt | — | R.6-Kioskfix falls TUI ok |
| React UI | **unknown** | fehlt | — | Nach Kiosk prüfen |
| WLAN | **unknown** | fehlt | — | R.6-WLANfix falls nötig |
| Netzwerk | **unknown** | fehlt | — | — |
| Telemetrie-Spool | **red** | `telemetry/` fehlt | Kein Boot | — |
| Telemetrie-Ingest | **gray** | fehlt | Kein LAN-Ingest erwartet offline | — |
| MSI-Hardware | **red** | `hardware/msi_*` fehlt | Kein Boot | MSI-Boot + Diagnose |
| interne Datenträger read-only | **unknown** | fehlt | — | Nach Boot |
| Backup-Ziel | **unknown** | fehlt | — | — |
| Restore-Gate | **unknown** | fehlt | — | — |
| Partitionshelfer read-only | **unknown** | fehlt | — | — |
| Logs | **red** | `boot/`, `menu/` fehlen | — | — |
| Evidence | **red** | Runtime-Baum fehlt | Hauptblocker | R.6-Persistencefix oder Bootfix |
| nächste Aktion | — | — | — | **MSI-Boot durchführen**, Stick erneut einlesen |

## Statische Vorab-Bewertung (Stick-Layout)

SquashFS im Image enthält R.3/R.4-Komponenten (R.5A PKFix bestätigt). Matrix kann erst nach Live-Boot geschrieben werden.

## Hinweis

Ohne `rescue_test_matrix_latest.json` ist keine Ampel-Auswertung aus Runtime möglich — alle Runtime-Bereiche **rot/unknown**.
