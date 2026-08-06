# GPU Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](GPU_BASELINE_DE.md) · [English](GPU_BASELINE_EN.md) · [Français](GPU_BASELINE_FR.md) · [Nederlands](GPU_BASELINE_NL.md)

Modul: `backend/core/gpu_baseline_diagnostics.py`

## Purpose

Describes purpose and limits of `backend/core/gpu_baseline_diagnostics.py` in the early baseline.

## Checked values

gpu_detection reuse, render nodes, kernel hang/reset, firmware load failures, optional glxinfo/eglinfo/vulkaninfo

## Not checked

render stress, driver/firmware install, blacklist/cmdline changes

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

kernel GPU hang/reset/fence timeout

## Yellow findings

driver missing, firmware missing, nomodeset, DRM/render node missing

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
