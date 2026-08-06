# Geheugen-baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Talen: [Deutsch](MEMORY_BASELINE_DE.md) · [English](MEMORY_BASELINE_EN.md) · [Français](MEMORY_BASELINE_FR.md) · [Nederlands](MEMORY_BASELINE_NL.md)

Modul: `backend/core/memory_baseline_diagnostics.py`

## Doel

Beschrijft doel en grenzen van `backend/core/memory_baseline_diagnostics.py` in de vroege baseline.

## Gecontroleerde waarden

meminfo, DMI RAM modules, EDAC/MCE/OOM, capacity plausibility, quick probe ≤128 MiB / 2% MemAvailable

## Niet gecontroleerd

full Memtest86+, ECC proof without DMI, long soak tests

## Statusbetekenis

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritieke bevindingen

uncorrected EDAC, MCE, quick-probe failed

## Gele bevindingen

corrected EDAC, OOM history, capacity mismatch, low MemAvailable

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
