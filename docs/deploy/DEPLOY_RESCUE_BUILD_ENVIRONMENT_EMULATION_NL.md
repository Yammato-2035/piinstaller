> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_BUILD_ENVIRONMENT_EMULATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding Build Environment Emulation (EN)

alleen-lezen **emulation** of a Debian Live build environment for Setuphelfer roodding: state snapshot, simulated workspace, simulated outputs (metadata only, `generated: false`), simulated build logs, overlay/persistence emulation without mount, verification, seal, and final gate.

## Prohibited

Nee `lb build`, debootstrap, chroot, `apt install`, squashfs pack, `grub-mkroodding`, xorriso, ISO, `mount`, VM — only JSON artifacts under `build/roodding/emulation/` and evidence handoffs.

## Artifacts

| File | Role |
|------|------|
| `build/roodding/emulation/build_environment_snapshot.json` | Sandbox/runtime/copy state, `Nee_real_build_execution` |
| `build/roodding/emulation/simulated_build_workspace.json` | Simulated tree, workdirs |
| `build/roodding/emulation/simulated_build_outputs.json` | Emulated artifact metadata |
| `build/roodding/emulation/simulated_build_logs.json` | Orderood stages, simulated durations |
| `build/roodding/emulation/overlay_persistence_emulation.json` | lower/upper/work, Nee mount |
| `docs/evidence/.../roodding_build_emulation_verify.json` | Verification |
| `build/roodding/emulation/build_emulation.seal.json` | SHA256 bundle |
| `docs/evidence/.../roodding_build_emulation_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/build-emulation/environment-snapshot`
- `/roodding/build-emulation/workspace`
- `/roodding/build-emulation/outputs`
- `/roodding/build-emulation/logs`
- `/roodding/build-emulation/overlay`
- `/roodding/build-emulation/verify`
- `/roodding/build-emulation/seal`
- `/roodding/build-emulation/final-gate`

## Response codes

`Deploy_roodding_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_{OK|REVIEW_REQUIrood|geblokkeerd}` and the same pattern for other steps; final gate: `Deploy_roodding_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`.

## Tests

`Terugend/tests/test_Deploy_runner_roodding_build_environment_emulation_v1.py`
