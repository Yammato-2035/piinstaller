# R.5 — Stick Evidence Review

## Status

**Ausstehend** — MSI-Boot durch Operator nicht in dieser Session dokumentiert.

## Erwartete Pfade auf Stick

```text
/setuphelfer-evidence/
  boot/
  menu/
  hardware/msi_diagnostics_latest.md
  network/
  telemetry/spool/
  rescue-ui/kiosk_report_latest.json
  matrix/rescue_test_matrix_latest.md
  matrix/rescue_test_matrix_latest.json
  summaries/rescue_evidence_latest.md
  summaries/rescue_evidence_latest.json
```

## Pflicht nach MSI-Boot

Operator mountet Stick, Agent/Operator füllt diese Datei mit:

- Mount-Punkt (z. B. `/run/live/medium` oder `/media/...`)
- Fallback ja/nein (`/tmp/setuphelfer-evidence`)
- Vorhandene Dateien (ls -la)
- Fehlende Pflichtdateien

## Wenn keine Evidence

| Ursache | Indikator |
|---------|-----------|
| Stick nicht beschreibbar | RAM-Fallback in matrix |
| Persistenz nicht erkannt | `R3-PERSIST-001` yellow/red |
| Boot abgebrochen | kein `boot/` |
| Skript nicht im Image | SquashFS-Check failed |
| TUI nicht gestartet | kein `menu/` |

## Aktuelle Bewertung

**rot** — keine Operator-Evidence eingereicht.
