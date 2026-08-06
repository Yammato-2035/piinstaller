# Baseline NVMe

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](NVME_BASELINE_DE.md) · [English](NVME_BASELINE_EN.md) · [Français](NVME_BASELINE_FR.md) · [Nederlands](NVME_BASELINE_NL.md)

Modul: `backend/core/nvme_baseline_diagnostics.py`

## Objectif

Décrit l'objectif et les limites de `backend/core/nvme_baseline_diagnostics.py` dans la baseline précoce.

## Valeurs vérifiées

nvme smart-log/id-ctrl: critical warning, available spare, percentage used, media errors, unsafe shutdowns, temperature; controller resets

## Propriétés non vérifiées

SMART self-test, firmware update, namespace format

## Signification des statuts

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Constats critiques

critical warning, spare below threshold, percentage used ≥100%, media errors, repeated controller resets

## Constats jaunes

high percentage used (≥80%), high temperature, unsafe shutdowns

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
