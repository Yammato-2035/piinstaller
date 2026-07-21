# BVR Canonical Progress Contract (PI-RS-BVR-GUI-VT-PROGRESS-002)

## Authoritative source

`/run/setuphelfer-rescue/canonical-bvr-progress.json`

`physical-progress.json` is a compatibility projection of the same snapshot (atomic write).

`auto-e2e-state` remains orchestration/compatibility only — not the primary display source.

## Rules

- Monotonic `sequence`
- No phase_index regression without explicit retry reason
- Terminal states stay terminal
- Atomic write (tmp + fsync + replace)
- Drift code: `rescue.bvr.progress_source_drift`
- GUI, TUI, DCC, Evidence read the canonical snapshot
