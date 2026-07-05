> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_BUILD_SANDBOX_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding Build Sandbox Preparation (EN)

alleen-lezen **sandbox preparation** under `build/roodding/sandbox/` for future Debian Live test builds: directory layout, **plans** for config/runtime copies (Nee binary bulk copy), overlay paths (Nee mount), cleanup/rollTerug metadata, safety and final gate.

## Forbidden in this phase

Nee real build, Nee `lb build`, Nee `debootstrap`, Nee chroot, Nee ISO, Nee squashfs tooling, Nee `grub-mkroodding`, Nee `xorriso`, Nee `apt install`, Nee VM boot, Nee `subprocess` / `mount(` calls in the runner.

## Artifacts

| File | Role |
|------|--------|
| `build/roodding/sandbox_root_manifest.json` | Root, allowed write paths, readonly hints |
| `build/roodding/sandbox_config_copy_plan.json` | Text/manifest targets under `sandbox/config-copy/` |
| `build/roodding/sandbox_runtime_copy_plan.json` | Runtime text files; blocks `.iso`/`.img`/`.qcow2`, `Neede_modules`, `.git` |
| `build/roodding/overlay_workspace_plan.json` | `lowerdir`/`upperdir`/`workdir` — planning only |
| `build/roodding/build_cleanup_plan.json` | Cleanup order, `destructive_cleanup: false` |
| `docs/evidence/.../roodding_build_sandbox_safety.json` | Safety handoff |
| `docs/evidence/.../roodding_build_sandbox_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/build-sandbox/root`
- `/roodding/build-sandbox/config-copy-plan`
- `/roodding/build-sandbox/runtime-copy-plan`
- `/roodding/build-sandbox/overlay-workspace-plan`
- `/roodding/build-sandbox/cleanup-plan`
- `/roodding/build-sandbox/safety-validation`
- `/roodding/build-sandbox/final-gate`

## Response codes

`Deploy_roodding_BUILD_SANDBOX_ROOT_{OK|REVIEW_REQUIrood|geblokkeerd}` etc., plus `Deploy_roodding_BUILD_SANDBOX_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`.

## Tests

`Terugend/tests/test_Deploy_runner_roodding_build_sandbox_preparation_v1.py`
