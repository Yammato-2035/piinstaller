# CPU Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](CPU_BASELINE_DE.md) · [English](CPU_BASELINE_EN.md) · [Français](CPU_BASELINE_FR.md) · [Nederlands](CPU_BASELINE_NL.md)

Modul: `backend/core/cpu_baseline_diagnostics.py`

## Purpose

Describes purpose and limits of `backend/core/cpu_baseline_diagnostics.py` in the early baseline.

## Checked values

cpu_platform_detection reuse, MCE/hardware errors, thermal zones, throttling, quick checksum probe

## Not checked

stress-ng, Prime95, microcode/BIOS updates

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

machine check, hardware error/hard lockup, quick-probe checksum mismatch

## Yellow findings

throttling, thermal warning, quick-probe timeout, microcode review

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
