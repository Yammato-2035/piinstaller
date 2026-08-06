# Baseline CPU

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](CPU_BASELINE_DE.md) · [English](CPU_BASELINE_EN.md) · [Français](CPU_BASELINE_FR.md) · [Nederlands](CPU_BASELINE_NL.md)

Modul: `backend/core/cpu_baseline_diagnostics.py`

## Objectif

Décrit l'objectif et les limites de `backend/core/cpu_baseline_diagnostics.py` dans la baseline précoce.

## Valeurs vérifiées

cpu_platform_detection reuse, MCE/hardware errors, thermal zones, throttling, quick checksum probe

## Propriétés non vérifiées

stress-ng, Prime95, microcode/BIOS updates

## Signification des statuts

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Constats critiques

machine check, hardware error/hard lockup, quick-probe checksum mismatch

## Constats jaunes

throttling, thermal warning, quick-probe timeout, microcode review

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
