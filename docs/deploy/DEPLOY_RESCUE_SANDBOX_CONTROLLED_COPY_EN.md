# Deploy — Rescue Sandbox Controlled Copy (EN)

Strictly bounded **execution** of prepared sandbox copy plans: only entries from `sandbox_config_copy_plan.json` / `sandbox_runtime_copy_plan.json`, destinations only under `build/rescue/sandbox/config-copy/` and `runtime-copy/`, SHA256 for source and target, atomic `.tmp` write, verification, seal, and final gate. **No** ISO build, live-build, debootstrap/chroot, apt install, mount, VM, dd/mkfs, systemctl, release/publish.

## Artifacts

| File | Role |
|------|------|
| `docs/evidence/.../rescue_sandbox_copy_execution_precheck.json` | Precheck (gates, safety, paths, size, symlinks) |
| `build/rescue/sandbox/manifests/config_copy_result.json` | Config copy outcome with hashes |
| `build/rescue/sandbox/manifests/runtime_copy_result.json` | Runtime copy outcome with hashes |
| `docs/evidence/.../rescue_sandbox_copy_verify_result.json` | Hash/plan/tree verification |
| `build/rescue/sandbox/manifests/sandbox_copy.seal.json` | SHA256 over result JSONs and verify handoff raw bytes |
| `docs/evidence/.../rescue_sandbox_copy_final_gate.json` | Aggregates precheck, verify, seal, branding, zero-state |

## API (`POST`, prefix `/api/deploy`)

- `/rescue/sandbox-copy/precheck`
- `/rescue/sandbox-copy/config`
- `/rescue/sandbox-copy/runtime`
- `/rescue/sandbox-copy/verify`
- `/rescue/sandbox-copy/seal`
- `/rescue/sandbox-copy/final-gate`

Request body: `explicit_overwrite` (bool) for handoff/result files.

## Response codes

`DEPLOY_RESCUE_SANDBOX_COPY_PRECHECK_{OK|REVIEW_REQUIRED|BLOCKED}` and the same pattern for `CONFIG`, `RUNTIME`, `VERIFY`, `SEAL`; final gate: `DEPLOY_RESCUE_SANDBOX_COPY_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_sandbox_controlled_copy_v1.py`
