# GPU-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](GPU_BASELINE_DE.md) · [English](GPU_BASELINE_EN.md) · [Français](GPU_BASELINE_FR.md) · [Nederlands](GPU_BASELINE_NL.md)

Modul: `backend/core/gpu_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/gpu_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

gpu_detection reuse, render nodes, kernel hang/reset, firmware load failures, optional glxinfo/eglinfo/vulkaninfo

## Nicht geprüfte Eigenschaften

render stress, driver/firmware install, blacklist/cmdline changes

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

kernel GPU hang/reset/fence timeout

## Gelbe Befunde

driver missing, firmware missing, nomodeset, DRM/render node missing

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
