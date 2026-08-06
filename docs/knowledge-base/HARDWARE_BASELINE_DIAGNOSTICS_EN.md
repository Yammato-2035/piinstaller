# Hardware Baseline Diagnostics

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Languages: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) · [English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) · [Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) · [Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

## Purpose

Short, safe risk check at rescue start for RAM, CPU, GPU and storage — before backup/restore/OS install/GUI are used.

## Checked values

Subsystem results, traffic-light severity, gate permissions (`backup_allowed`, `restore_allowed`, `os_installation_allowed`, `gui_mode_allowed`), issue codes.

## Not checked

No long-term stability claims, no fault-free guarantee, no automatic self/stress tests, no driver/firmware install.

## Status meaning

`no_immediate_issue_detected` / `immediate_issue_detected` / `review_required` / `test_unavailable` / `not_tested` — never "healthy/passed".

## Critical findings

Red memory/CPU/storage findings block restore and OS installation.

## Yellow findings

Yellow findings produce `review_required` and recommend extended tests.

## Safe next steps

First rescue source data, then review flagged components; GUI only with a stable GPU.

## Limits

Green ≠ fault-free. Missing tools yield gray/`test_unavailable`, never fake green.

## Evidence

API: `/api/rescue/hardware/baseline/*`. Unit tests under `backend/tests/test_*baseline*_v1.py`.

## Privacy

No serial numbers/MAC/IP in telemetry. Only redacted status summaries.

## Extended diagnosis

Memtest86+, CPU stress, GPU render stress, SMART self-test — only with operator confirmation.
