# Erweiterte Hardwaretests

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](EXTENDED_HARDWARE_TESTS_DE.md) · [English](EXTENDED_HARDWARE_TESTS_EN.md) · [Français](EXTENDED_HARDWARE_TESTS_FR.md) · [Nederlands](EXTENDED_HARDWARE_TESTS_NL.md)

Modul: `ExtendedTestRecommendation in hardware_baseline_contracts.py`

## Zweck

Beschreibt Zweck und Grenzen von `ExtendedTestRecommendation in hardware_baseline_contracts.py` in der frühen Baseline.

## Geprüfte Werte

preview only: recommended/required, test_type, estimated_duration, operator_confirmation_required=true

## Nicht geprüfte Eigenschaften

no automatic start of Memtest86+, stress-ng, GPU render stress, SMART self-test in this phase

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

required=true for critical memory/storage findings before restore/install trust

## Gelbe Befunde

recommended=true for degraded/review cases

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
