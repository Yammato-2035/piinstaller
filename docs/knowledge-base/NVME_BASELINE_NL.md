# NVMe-baseline

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Talen: [Deutsch](NVME_BASELINE_DE.md) · [English](NVME_BASELINE_EN.md) · [Français](NVME_BASELINE_FR.md) · [Nederlands](NVME_BASELINE_NL.md)

Modul: `backend/core/nvme_baseline_diagnostics.py`

## Doel

Beschrijft doel en grenzen van `backend/core/nvme_baseline_diagnostics.py` in de vroege baseline.

## Gecontroleerde waarden

nvme smart-log/id-ctrl: critical warning, available spare, percentage used, media errors, unsafe shutdowns, temperature; controller resets

## Niet gecontroleerd

SMART self-test, firmware update, namespace format

## Statusbetekenis

Uses BaselineStatus vocabulary (`no_immediate_issue_detected`, `immediate_issue_detected`, `review_required`, `test_unavailable`, `not_tested`). Never claims hardware is fault-free.

## Kritieke bevindingen

critical warning, spare below threshold, percentage used ≥100%, media errors, repeated controller resets

## Gele bevindingen

high percentage used (≥80%), high temperature, unsafe shutdowns

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
