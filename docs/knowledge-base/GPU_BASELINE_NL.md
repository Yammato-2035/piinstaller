# GPU-baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Talen: [Deutsch](GPU_BASELINE_DE.md) · [English](GPU_BASELINE_EN.md) · [Français](GPU_BASELINE_FR.md) · [Nederlands](GPU_BASELINE_NL.md)

Modul: `backend/core/gpu_baseline_diagnostics.py`

## Doel

Beschrijft doel en grenzen van `backend/core/gpu_baseline_diagnostics.py` in de vroege baseline.

## Gecontroleerde waarden

gpu_detection reuse, render nodes, kernel hang/reset, firmware load failures, optional glxinfo/eglinfo/vulkaninfo

## Niet gecontroleerd

render stress, driver/firmware install, blacklist/cmdline changes

## Statusbetekenis

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritieke bevindingen

kernel GPU hang/reset/fence timeout

## Gele bevindingen

driver missing, firmware missing, nomodeset, DRM/render node missing

## Veilige volgende stappen

Rescue source data first. Do not restore/install onto red targets. Prefer TUI if GPU is red. Start extended tests only with operator confirmation.

## Grenzen

Short read-only / bounded probes only. Missing tools → gray/`test_unavailable`, never fake green.

## Evidence

API routes under `/api/rescue/hardware/baseline/`. Related unit tests in `backend/tests/`.

## Privacy

No serial numbers, MAC addresses or IP addresses in telemetry payloads.

## Uitgebreide diagnose

Extended tests are preview-only (`ExtendedTestRecommendation`). Automatic start is forbidden in this phase.
