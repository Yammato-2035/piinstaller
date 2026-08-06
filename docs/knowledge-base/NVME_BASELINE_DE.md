# NVMe-Baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Sprachen: [Deutsch](NVME_BASELINE_DE.md) · [English](NVME_BASELINE_EN.md) · [Français](NVME_BASELINE_FR.md) · [Nederlands](NVME_BASELINE_NL.md)

Modul: `backend/core/nvme_baseline_diagnostics.py`

## Zweck

Beschreibt Zweck und Grenzen von `backend/core/nvme_baseline_diagnostics.py` in der frühen Baseline.

## Geprüfte Werte

nvme smart-log/id-ctrl: critical warning, available spare, percentage used, media errors, unsafe shutdowns, temperature; controller resets

## Nicht geprüfte Eigenschaften

SMART self-test, firmware update, namespace format

## Statusbedeutung

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritische Befunde

critical warning, spare below threshold, percentage used ≥100%, media errors, repeated controller resets

## Gelbe Befunde

high percentage used (≥80%), high temperature, unsafe shutdowns

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
