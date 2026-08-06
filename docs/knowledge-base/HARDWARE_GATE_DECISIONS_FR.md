# Décisions du gate matériel

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Langues: [Deutsch](HARDWARE_GATE_DECISIONS_DE.md) · [English](HARDWARE_GATE_DECISIONS_EN.md) · [Français](HARDWARE_GATE_DECISIONS_FR.md) · [Nederlands](HARDWARE_GATE_DECISIONS_NL.md)

Modul: `backend/rescue/hardware_baseline_gate.py`

## Objectif

Décrit l'objectif et les limites de `backend/rescue/hardware_baseline_gate.py` dans la baseline précoce.

## Valeurs vérifiées

aggregates subsystem statuses into gate.status and operation permissions; evaluate_operation_against_baseline_gate adds source/target roles

## Propriétés non vérifiées

does not replace safety_facade; never writes; never bypasses write-target validation

## Signification des statuts

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Constats critiques

blocked: restore/os_installation false; gui_mode false on red GPU; red target blocks backup write

## Constats jaunes

review_required; GUI still allowed with yellow GPU; backup remains allowed

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
