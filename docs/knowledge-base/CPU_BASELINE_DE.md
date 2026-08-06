# CPU-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](CPU_BASELINE_DE.md) · [English](CPU_BASELINE_EN.md) · [Français](CPU_BASELINE_FR.md) · [Nederlands](CPU_BASELINE_NL.md)

Modul: `backend/core/cpu_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/cpu_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

cpu_platform_detection reuse, MCE/hardware errors, thermal zones, throttling, quick checksum probe

## Nicht geprüfte Eigenschaften

stress-ng, Prime95, microcode/BIOS updates

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

machine check, hardware error/hard lockup, quick-probe checksum mismatch

## Gelbe Befunde

throttling, thermal warning, quick-probe timeout, microcode review

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
