> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_BUILD_SANDBOX_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours Build Sandbox Preparation (EN)

lecture seule **sandbox preparation** under `build/Secours/sandbox/` for future Debian Live test builds: directory layout, **plans** for config/runtime copies (Non binary bulk copy), overlay paths (Non mount), cleanup/rollRetour metadata, safety and final gate.

## Forbidden in this phase

Non real build, Non `lb build`, Non `debootstrap`, Non chroot, Non ISO, Non squashfs tooling, Non `grub-mkSecours`, Non `xorriso`, Non `apt install`, Non VM boot, Non `subprocess` / `mount(` calls in the runner.

## Artifacts

| File | Role |
|------|--------|
| `build/Secours/sandbox_root_manifest.json` | Root, allowed write paths, readonly hints |
| `build/Secours/sandbox_config_copy_plan.json` | Text/manifest targets under `sandbox/config-copy/` |
| `build/Secours/sandbox_runtime_copy_plan.json` | Runtime text files; blocks `.iso`/`.img`/`.qcow2`, `Nonde_modules`, `.git` |
| `build/Secours/overlay_workspace_plan.json` | `lowerdir`/`upperdir`/`workdir` — planning only |
| `build/Secours/build_cleanup_plan.json` | Cleanup order, `destructive_cleanup: false` |
| `docs/evidence/.../Secours_build_sandbox_safety.json` | Safety handoff |
| `docs/evidence/.../Secours_build_sandbox_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/build-sandbox/root`
- `/Secours/build-sandbox/config-copy-plan`
- `/Secours/build-sandbox/runtime-copy-plan`
- `/Secours/build-sandbox/overlay-workspace-plan`
- `/Secours/build-sandbox/cleanup-plan`
- `/Secours/build-sandbox/safety-validation`
- `/Secours/build-sandbox/final-gate`

## Response codes

`Déploiement_Secours_BUILD_SANDBOX_ROOT_{OK|REVIEW_REQUIrouge|bloqué}` etc., plus `Déploiement_Secours_BUILD_SANDBOX_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`.

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_build_sandbox_preparation_v1.py`
