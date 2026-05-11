# Deploy — Rescue Build Sandbox Preparation (EN)

Read-only **sandbox preparation** under `build/rescue/sandbox/` for future Debian Live test builds: directory layout, **plans** for config/runtime copies (no binary bulk copy), overlay paths (no mount), cleanup/rollback metadata, safety and final gate.

## Forbidden in this phase

No real build, no `lb build`, no `debootstrap`, no chroot, no ISO, no squashfs tooling, no `grub-mkrescue`, no `xorriso`, no `apt install`, no VM boot, no `subprocess` / `mount(` calls in the runner.

## Artifacts

| File | Role |
|------|--------|
| `build/rescue/sandbox_root_manifest.json` | Root, allowed write paths, readonly hints |
| `build/rescue/sandbox_config_copy_plan.json` | Text/manifest targets under `sandbox/config-copy/` |
| `build/rescue/sandbox_runtime_copy_plan.json` | Runtime text files; blocks `.iso`/`.img`/`.qcow2`, `node_modules`, `.git` |
| `build/rescue/overlay_workspace_plan.json` | `lowerdir`/`upperdir`/`workdir` — planning only |
| `build/rescue/build_cleanup_plan.json` | Cleanup order, `destructive_cleanup: false` |
| `docs/evidence/.../rescue_build_sandbox_safety.json` | Safety handoff |
| `docs/evidence/.../rescue_build_sandbox_final_gate.json` | Final gate |

## API (`POST`, prefix `/api/deploy`)

- `/rescue/build-sandbox/root`
- `/rescue/build-sandbox/config-copy-plan`
- `/rescue/build-sandbox/runtime-copy-plan`
- `/rescue/build-sandbox/overlay-workspace-plan`
- `/rescue/build-sandbox/cleanup-plan`
- `/rescue/build-sandbox/safety-validation`
- `/rescue/build-sandbox/final-gate`

## Response codes

`DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_{OK|REVIEW_REQUIRED|BLOCKED}` etc., plus `DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_build_sandbox_preparation_v1.py`
