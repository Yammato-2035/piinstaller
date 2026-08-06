# Hardware-Gate-Entscheidungen

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](HARDWARE_GATE_DECISIONS_DE.md) · [English](HARDWARE_GATE_DECISIONS_EN.md) · [Français](HARDWARE_GATE_DECISIONS_FR.md) · [Nederlands](HARDWARE_GATE_DECISIONS_NL.md)

Modul: `backend/rescue/hardware_baseline_gate.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/rescue/hardware_baseline_gate.py` in der frühen Baseline.

## Geprüfte Werte

aggregates subsystem statuses into gate.status and operation permissions; evaluate_operation_against_baseline_gate adds source/target roles

## Nicht geprüfte Eigenschaften

does not replace safety_facade; never writes; never bypasses write-target validation

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

blocked: restore/os_installation false; gui_mode false on red GPU; red target blocks backup write

## Gelbe Befunde

review_required; GUI still allowed with yellow GPU; backup remains allowed

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
