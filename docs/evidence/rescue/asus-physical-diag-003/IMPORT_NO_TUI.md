# Import nach Stick-Rückkehr — keine TUI

## Befund

- Stick Ultra Line `/dev/sda` mit Payload **1.10.2.0** auf ESP.
- **Keine** Dateien neuer als Inject → kein erfolgreicher Boot mit neuem Capture.
- Letzter Boot: `503549ad-…` am 2026-07-22T18:50Z, Payload **1.10.1.2**.
- Cmdline: Lab-Auto **GUI** + `msi_lab_auto` + `msi_e2e_auto` + `auto_shutdown`.
- `text_mode_started=false` → erklärt „keine TUI“.

## Import

- Identity: ASUS G513QM match, MSI ausgeschlossen, kein newest-session-Fallback.
- Ergebnis: `imported_partial_no_new_hardware_discovery`
- Endstatus: `diagnosis_incomplete`
- Run: `physical_runs/import-gabriel-503549ad-no-new-boot/`

## Korrektur am Stick (nach Import)

- GRUB `default` auf Eintrag **ASUS Hardwarediagnose (nur Lesen)** gesetzt, `timeout=20`.

## Stick-Korrektur ausgeführt

- `set default=13` → ASUS Hardwarediagnose (nur Lesen)
- `set timeout=20`
