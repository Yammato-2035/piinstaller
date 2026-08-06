# Hardware Gate Decisions

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](HARDWARE_GATE_DECISIONS_DE.md) · [English](HARDWARE_GATE_DECISIONS_EN.md) · [Français](HARDWARE_GATE_DECISIONS_FR.md) · [Nederlands](HARDWARE_GATE_DECISIONS_NL.md)

Modul: `backend/rescue/hardware_baseline_gate.py`

## Purpose

Describes purpose and limits of `backend/rescue/hardware_baseline_gate.py` in the early baseline.

## Checked values

aggregates subsystem statuses into gate.status and operation permissions; evaluate_operation_against_baseline_gate adds source/target roles

## Not checked

does not replace safety_facade; never writes; never bypasses write-target validation

## Status meaning

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Critical findings

blocked: restore/os_installation false; gui_mode false on red GPU; red target blocks backup write

## Yellow findings

review_required; GUI still allowed with yellow GPU; backup remains allowed

## Safe next steps

Rescue source data first. Do not restore/install onto red targets. Prefer TUI if GPU is red. Start extended tests only with operator confirmation.

## Limits

Short read-only / bounded probes only. Missing tools → gray/`test_unavailable`, never fake green.

## Evidence

API routes under `/api/rescue/hardware/baseline/`. Related unit tests in `backend/tests/`.

## Privacy

No serial numbers, MAC addresses or IP addresses in telemetry payloads.

## Extended diagnosis

Extended tests are preview-only (`ExtendedTestRecommendation`). Automatic start is forbidden in this phase.
