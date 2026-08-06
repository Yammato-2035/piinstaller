# Extended Hardware Tests

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](EXTENDED_HARDWARE_TESTS_DE.md) · [English](EXTENDED_HARDWARE_TESTS_EN.md) · [Français](EXTENDED_HARDWARE_TESTS_FR.md) · [Nederlands](EXTENDED_HARDWARE_TESTS_NL.md)

Modul: `ExtendedTestRecommendation in hardware_baseline_contracts.py`

## Purpose

Describes purpose and limits of `ExtendedTestRecommendation in hardware_baseline_contracts.py` in the early baseline.

## Checked values

preview only: recommended/required, test_type, estimated_duration, operator_confirmation_required=true

## Not checked

no automatic start of Memtest86+, stress-ng, GPU render stress, SMART self-test in this phase

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

required=true for critical memory/storage findings before restore/install trust

## Yellow findings

recommended=true for degraded/review cases

## Safe next steps

Rescue source data first. Do not restore/install onto red targets. Prefer TUI if GPU is red. Start extended tests only with operator confirmation.

## Limits

Short read-only / bounded probes only. Missing tools → gray/`test_unavailable`, never fake green.

## Evidence

API routes under `/api/rescue/hardware/baseline/`. Related unit tests in `backend/tests/`.

## Privacy

No serial numbers, MAC addresses or IP addresses in telemetry payloads.

## Extended diagnosis

Extended tests are preview-only (`ExtendedTestRecommendation`). Automatic start is forbidden in this phase.
