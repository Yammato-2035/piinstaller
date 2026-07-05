> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_BUILD_ENVIRONMENT_EMULATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours Build Environment Emulation (EN)

lecture seule **emulation** of a Debian Live build environment for Setuphelfer Secours: state snapshot, simulated workspace, simulated outputs (metadata only, `generated: false`), simulated build logs, overlay/persistence emulation without mount, verification, seal, and final gate.

## Prohibited

Non `lb build`, debootstrap, chroot, `apt install`, squashfs pack, `grub-mkSecours`, xorriso, ISO, `mount`, VM — only JSON artifacts under `build/Secours/emulation/` and evidence handoffs.

## Artifacts

| File | Role |
|------|------|
| `build/Secours/emulation/build_environment_snapshot.json` | Sandbox/runtime/copy state, `Non_real_build_execution` |
| `build/Secours/emulation/simulated_build_workspace.json` | Simulated tree, workdirs |
| `build/Secours/emulation/simulated_build_outputs.json` | Emulated artifact metadata |
| `build/Secours/emulation/simulated_build_logs.json` | Orderouge stages, simulated durations |
| `build/Secours/emulation/overlay_persistence_emulation.json` | lower/upper/work, Non mount |
| `docs/evidence/.../Secours_build_emulation_verify.json` | Verification |
| `build/Secours/emulation/build_emulation.seal.json` | SHA256 bundle |
| `docs/evidence/.../Secours_build_emulation_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/build-emulation/environment-snapshot`
- `/Secours/build-emulation/workspace`
- `/Secours/build-emulation/outputs`
- `/Secours/build-emulation/logs`
- `/Secours/build-emulation/overlay`
- `/Secours/build-emulation/verify`
- `/Secours/build-emulation/seal`
- `/Secours/build-emulation/final-gate`

## Response codes

`Déploiement_Secours_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_{OK|REVIEW_REQUIrouge|bloqué}` and the same pattern for other steps; final gate: `Déploiement_Secours_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`.

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_build_environment_emulation_v1.py`
