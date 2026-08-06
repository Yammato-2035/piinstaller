# Hardware-Baseline-Diagnostik

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) · [English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) · [Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) · [Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

## Zweck

Kurzer, sicherer Risikocheck beim Rescue-Start für RAM, CPU, GPU und Storage — bevor Backup/Restore/OS-Install/GUI genutzt werden.

## Geprüfte Werte

Subsystem-Ergebnisse, Ampel-Severity, Gate-Permissions (`backup_allowed`, `restore_allowed`, `os_installation_allowed`, `gui_mode_allowed`), Issue-Codes.

## Nicht geprüfte Eigenschaften

Keine Langzeitstabilität, keine Funktionsgarantie, keine automatischen Self-/Stress-Tests, keine Treiber-/Firmware-Installation.

## Statusbedeutung

`no_immediate_issue_detected` / `immediate_issue_detected` / `review_required` / `test_unavailable` / `not_tested` — nie „healthy/passed“.

## Kritische Befunde

Rote Memory-/CPU-/Storage-Befunde blockieren Restore und OS-Installation.

## Gelbe Befunde

Gelbe Befunde erzeugen `review_required` und empfehlen erweiterte Tests.

## Sichere nächste Schritte

Zuerst Quelldaten sichern, dann auffällige Komponenten prüfen, GUI nur bei stabiler GPU.

## Grenzen

Grün ≠ fehlerfrei. Fehlende Tools ergeben Grau/`test_unavailable`, nie Fake-Green.

## Evidence

API: `/api/rescue/hardware/baseline/*`. Unit-Tests unter `backend/tests/test_*baseline*_v1.py`.

## Datenschutz

Keine Seriennummern/MAC/IP in Telemetrie. Nur redigierte Statuszusammenfassungen.

## Erweiterte Diagnose

Memtest86+, CPU-Stress, GPU-Render-Stress, SMART Self-Test — nur mit Operatorbestätigung.
