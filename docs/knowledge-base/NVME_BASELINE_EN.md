# NVMe Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](NVME_BASELINE_DE.md) · [English](NVME_BASELINE_EN.md) · [Français](NVME_BASELINE_FR.md) · [Nederlands](NVME_BASELINE_NL.md)

Modul: `backend/core/nvme_baseline_diagnostics.py`

## Purpose

Describes purpose and limits of `backend/core/nvme_baseline_diagnostics.py` in the early baseline.

## Checked values

nvme smart-log/id-ctrl: critical warning, available spare, percentage used, media errors, unsafe shutdowns, temperature; controller resets

## Not checked

SMART self-test, firmware update, namespace format

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

critical warning, spare below threshold, percentage used ≥100%, media errors, repeated controller resets

## Yellow findings

high percentage used (≥80%), high temperature, unsafe shutdowns

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
