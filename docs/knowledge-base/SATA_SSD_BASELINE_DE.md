# SATA-SSD-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](SATA_SSD_BASELINE_DE.md) · [English](SATA_SSD_BASELINE_EN.md) · [Français](SATA_SSD_BASELINE_FR.md) · [Nederlands](SATA_SSD_BASELINE_NL.md)

Modul: `backend/core/sata_ssd_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/sata_ssd_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

wear leveling, reserved space, reported uncorrectable, CRC, unsafe shutdowns, TRIM via discard_granularity

## Nicht geprüfte Eigenschaften

SMART self-test start, vendor proprietary tools, secure erase

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

low reserved space, uncorrectable errors, SMART FAILED, repeated I/O errors

## Gelbe Befunde

wear warning, CRC errors, unsafe shutdowns

## Sichere nächste Schritte

Rescue source data first. Do not restore/install onto red targets. Prefer TUI if GPU is red. Start extended tests only with operator confirmation.

## Grenzen

Short read-only / bounded probes only. Missing tools → gray/`test_unavailable`, never fake green.

## Evidence

API routes under `/api/rescue/hardware/baseline/`. Related unit tests in `backend/tests/`.

## Datenschutz

No serial numbers, MAC addresses or IP addresses in telemetry payloads.

## Erweiterte Diagnose

Extended tests are preview-only (`ExtendedTestRecommendation`). Automatic start is forbidden in this phase.
