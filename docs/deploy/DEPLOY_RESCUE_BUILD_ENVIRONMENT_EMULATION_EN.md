# Deploy — Rescue Build Environment Emulation (EN)

Read-only **emulation** of a Debian Live build environment for Setuphelfer Rescue: state snapshot, simulated workspace, simulated outputs (metadata only, `generated: false`), simulated build logs, overlay/persistence emulation without mount, verification, seal, and final gate.

## Prohibited

No `lb build`, debootstrap, chroot, `apt install`, squashfs pack, `grub-mkrescue`, xorriso, ISO, `mount`, VM — only JSON artifacts under `build/rescue/emulation/` and evidence handoffs.

## Artifacts

| File | Role |
|------|------|
| `build/rescue/emulation/build_environment_snapshot.json` | Sandbox/runtime/copy state, `no_real_build_execution` |
| `build/rescue/emulation/simulated_build_workspace.json` | Simulated tree, workdirs |
| `build/rescue/emulation/simulated_build_outputs.json` | Emulated artifact metadata |
| `build/rescue/emulation/simulated_build_logs.json` | Ordered stages, simulated durations |
| `build/rescue/emulation/overlay_persistence_emulation.json` | lower/upper/work, no mount |
| `docs/evidence/.../rescue_build_emulation_verify.json` | Verification |
| `build/rescue/emulation/build_emulation.seal.json` | SHA256 bundle |
| `docs/evidence/.../rescue_build_emulation_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/deploy`)

- `/rescue/build-emulation/environment-snapshot`
- `/rescue/build-emulation/workspace`
- `/rescue/build-emulation/outputs`
- `/rescue/build-emulation/logs`
- `/rescue/build-emulation/overlay`
- `/rescue/build-emulation/verify`
- `/rescue/build-emulation/seal`
- `/rescue/build-emulation/final-gate`

## Response codes

`DEPLOY_RESCUE_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_{OK|REVIEW_REQUIRED|BLOCKED}` and the same pattern for other steps; final gate: `DEPLOY_RESCUE_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_build_environment_emulation_v1.py`
