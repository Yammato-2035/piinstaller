# Baseline mémoire

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](MEMORY_BASELINE_DE.md) · [English](MEMORY_BASELINE_EN.md) · [Français](MEMORY_BASELINE_FR.md) · [Nederlands](MEMORY_BASELINE_NL.md)

Modul: `backend/core/memory_baseline_diagnostics.py`

## Objectif

Décrit l'objectif et les limites de `backend/core/memory_baseline_diagnostics.py` dans la baseline précoce.

## Valeurs vérifiées

meminfo, DMI RAM modules, EDAC/MCE/OOM, capacity plausibility, quick probe ≤128 MiB / 2% MemAvailable

## Propriétés non vérifiées

full Memtest86+, ECC proof without DMI, long soak tests

## Signification des statuts

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Constats critiques

uncorrected EDAC, MCE, quick-probe failed

## Constats jaunes

corrected EDAC, OOM history, capacity mismatch, low MemAvailable

## Prochaines étapes sûres

Rescue source data first. Do not restore/install onto red targets. Prefer TUI if GPU is red. Start extended tests only with operator confirmation.

## Limites

Short read-only / bounded probes only. Missing tools → gray/`test_unavailable`, never fake green.

## Evidence

API routes under `/api/rescue/hardware/baseline/`. Related unit tests in `backend/tests/`.

## Confidentialité

No serial numbers, MAC addresses or IP addresses in telemetry payloads.

## Diagnostic étendu

Extended tests are preview-only (`ExtendedTestRecommendation`). Automatic start is forbidden in this phase.
