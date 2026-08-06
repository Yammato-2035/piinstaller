# Memory Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](MEMORY_BASELINE_DE.md) · [English](MEMORY_BASELINE_EN.md) · [Français](MEMORY_BASELINE_FR.md) · [Nederlands](MEMORY_BASELINE_NL.md)

Modul: `backend/core/memory_baseline_diagnostics.py`

## Purpose

Describes purpose and limits of `backend/core/memory_baseline_diagnostics.py` in the early baseline.

## Checked values

meminfo, DMI RAM modules, EDAC/MCE/OOM, capacity plausibility, quick probe ≤128 MiB / 2% MemAvailable

## Not checked

full Memtest86+, ECC proof without DMI, long soak tests

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

uncorrected EDAC, MCE, quick-probe failed

## Yellow findings

corrected EDAC, OOM history, capacity mismatch, low MemAvailable

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
