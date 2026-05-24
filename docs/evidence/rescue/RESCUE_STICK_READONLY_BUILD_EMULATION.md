# Rescue stick — read-only build emulation (evidence)

**Date:** 2026-05-24  
**Runner:** `backend/deploy/runner_rescue_stick_readonly_build_emulation.py`

## Scope

Emulation only — no ISO, no `lb build`, no debootstrap/chroot/apt/mount/qemu/dd.

## Outputs

| Path | Purpose |
|------|---------|
| `build/rescue/emulation/rescue_stick_*.json` | Seven preview artifacts |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json` | SHA256 manifest + scans |
| `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json` | Aggregated gate |

## Verification

- Unit tests: `backend/tests/test_deploy_runner_rescue_stick_readonly_build_emulation_v1.py` (15 cases)
- Deploy docs: `docs/deploy/RESCUE_STICK_READONLY_BUILD_EMULATION_DE.md`

## Operator

Regenerate with API `POST /api/deploy/rescue-stick/build-emulation/run-all` and `explicit_overwrite: true` after gate doc updates.
