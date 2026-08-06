# SATA SSD Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](SATA_SSD_BASELINE_DE.md) · [English](SATA_SSD_BASELINE_EN.md) · [Français](SATA_SSD_BASELINE_FR.md) · [Nederlands](SATA_SSD_BASELINE_NL.md)

Modul: `backend/core/sata_ssd_baseline_diagnostics.py`

## Purpose

Describes purpose and limits of `backend/core/sata_ssd_baseline_diagnostics.py` in the early baseline.

## Checked values

wear leveling, reserved space, reported uncorrectable, CRC, unsafe shutdowns, TRIM via discard_granularity

## Not checked

SMART self-test start, vendor proprietary tools, secure erase

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

low reserved space, uncorrectable errors, SMART FAILED, repeated I/O errors

## Yellow findings

wear warning, CRC errors, unsafe shutdowns

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
