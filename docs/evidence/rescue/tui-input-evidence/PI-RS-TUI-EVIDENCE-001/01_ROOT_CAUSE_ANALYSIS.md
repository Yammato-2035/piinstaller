# Root cause analysis

## Hypothesis

`resolve_evidence_root()` called `resolve_setup_logs(allow_mount=False)` early.
When SETUP_LOGS was not yet mounted, evidence fell back to
`/run/setuphelfer/tui-input-diagnostics/`. `finalize_run_dir()` only wrote into the
current run directory and never migrated to SETUP_LOGS. On reboot, `/run` was lost.

## Checks

1. Start used `allow_mount=False` — **yes** (old code).
2. Why — safety: diagnose start must not block on mount; also avoided auto-mount at start.
3. Conscious safety choice for start path — **yes**; missing migrate was the bug.
4. Later resolver call — **no** before this fix.
5. Fallback path stored — **yes** under `/run`.
6. Finalizer knew `/run` — **no**.
7. Finalizer re-resolved SETUP_LOGS — **no**.
8. Migration step — **missing**.
9. Called on all end paths — **N/A** (absent).
10. Shutdown persistence check — **no**.
11. End paths all lost `/run` on reboot.
12. Runtime deleted early — **no** (lost via reboot instead).
13. Race: diagnose vs late SETUP_LOGS mount vs shutdown — **confirmed by lab runs 2/3**.

## Reproduction

Unit regression `test_old_pattern_loss_simulated_then_fixed`:
- old pattern: runtime finalize only → no persistent dir
- new pattern: wait + `.partial` publish → persisted + shutdown allowed

## Status

**confirmed** (old loss simulated; fix turns same scenario green)
