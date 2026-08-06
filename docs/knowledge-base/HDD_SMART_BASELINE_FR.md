# Baseline SMART HDD

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](HDD_SMART_BASELINE_DE.md) · [English](HDD_SMART_BASELINE_EN.md) · [Français](HDD_SMART_BASELINE_FR.md) · [Nederlands](HDD_SMART_BASELINE_NL.md)

Modul: `backend/core/hdd_baseline_diagnostics.py`

## Objectif

Décrit l'objectif et les limites de `backend/core/hdd_baseline_diagnostics.py` dans la baseline précoce.

## Valeurs vérifiées

smartctl -H/-A: pending, offline uncorrectable, reallocated, UDMA CRC, temperature; kernel I/O errors

## Propriétés non vérifiées

SMART self-test start, surface scan, destructive writes

## Signification des statuts

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Constats critiques

SMART FAILED, pending/offline uncorrectable, repeated I/O errors

## Constats jaunes

reallocated sectors, CRC errors, high temperature

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
