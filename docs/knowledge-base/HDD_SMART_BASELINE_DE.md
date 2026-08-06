# HDD-SMART-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](HDD_SMART_BASELINE_DE.md) · [English](HDD_SMART_BASELINE_EN.md) · [Français](HDD_SMART_BASELINE_FR.md) · [Nederlands](HDD_SMART_BASELINE_NL.md)

Modul: `backend/core/hdd_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/hdd_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

smartctl -H/-A: pending, offline uncorrectable, reallocated, UDMA CRC, temperature; kernel I/O errors

## Nicht geprüfte Eigenschaften

SMART self-test start, surface scan, destructive writes

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

SMART FAILED, pending/offline uncorrectable, repeated I/O errors

## Gelbe Befunde

reallocated sectors, CRC errors, high temperature

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
