# Rescue stick — read-only build emulation (KB)

## Purpose

Prepare a **complete emulation pass** before any real Debian live / ISO work. All outputs are JSON under `build/rescue/emulation/` and `docs/evidence/runtime-results/handoff/` with:

- `generated: false`
- `readonly_emulated: true`
- `no_real_build_execution: true`

## Runner

`backend/deploy/runner_rescue_stick_readonly_build_emulation.py`

## Gates

Contract: `docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md`

Final handoff: `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json`

## Post-deploy (2026-05-24)

| Topic | Decision |
|-------|----------|
| Network stack | systemd-networkd default; NM optional_later; live OS test pending |
| Offline fonts | No Google Fonts in source; system fonts; redeploy dist for runtime |
| systemd | localhost bind; no auto restore/partition |
| LAN | local_only; LAN blocked; auth required before future LAN |

Final gate: **review_required** (package_list; runtime frontend until redeploy). See `docs/evidence/rescue/RESCUE_STICK_READONLY_BUILD_EMULATION.md`.

## Next step

Operator redeploy (`deploy-to-opt.sh`), then runtime `run-all`. Real ISO only after live OS network validation and CDN-free dist — **separate** gated task.
