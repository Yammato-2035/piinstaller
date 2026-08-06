# Arbeitsspeicher-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](MEMORY_BASELINE_DE.md) · [English](MEMORY_BASELINE_EN.md) · [Français](MEMORY_BASELINE_FR.md) · [Nederlands](MEMORY_BASELINE_NL.md)

Modul: `backend/core/memory_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/memory_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

meminfo, DMI RAM modules, EDAC/MCE/OOM, capacity plausibility, quick probe ≤128 MiB / 2% MemAvailable

## Nicht geprüfte Eigenschaften

full Memtest86+, ECC proof without DMI, long soak tests

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

uncorrected EDAC, MCE, quick-probe failed

## Gelbe Befunde

corrected EDAC, OOM history, capacity mismatch, low MemAvailable

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
