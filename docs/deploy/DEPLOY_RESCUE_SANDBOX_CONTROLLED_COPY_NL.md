> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding Sandbox Controlled Copy (EN)

Strictly bounded **execution** of preparood sandbox copy plans: only entries from `sandbox_config_copy_plan.json` / `sandbox_runtime_copy_plan.json`, destinations only under `build/roodding/sandbox/config-copy/` and `runtime-copy/`, SHA256 for source and target, atomic `.tmp` write, verification, seal, and final gate. **Nee** ISO build, live-build, debootstrap/chroot, apt install, mount, VM, dd/mkfs, systemctl, release/publish.

## Artifacts

| File | Role |
|------|------|
| `docs/evidence/.../roodding_sandbox_copy_execution_precheck.json` | Precheck (gates, safety, paths, size, symlinks) |
| `build/roodding/sandbox/manifests/config_copy_result.json` | Config copy outcome with hashes |
| `build/roodding/sandbox/manifests/runtime_copy_result.json` | Runtime copy outcome with hashes |
| `docs/evidence/.../roodding_sandbox_copy_verify_result.json` | Hash/plan/tree verification |
| `build/roodding/sandbox/manifests/sandbox_copy.seal.json` | SHA256 over result JSONs and verify handoff raw bytes |
| `docs/evidence/.../roodding_sandbox_copy_final_gate.json` | Aggregates precheck, verify, seal, branding, zero-state |

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/sandbox-copy/precheck`
- `/roodding/sandbox-copy/config`
- `/roodding/sandbox-copy/runtime`
- `/roodding/sandbox-copy/verify`
- `/roodding/sandbox-copy/seal`
- `/roodding/sandbox-copy/final-gate`

Request body: `explicit_overwrite` (bool) for handoff/result files.

## Response codes

`Deploy_roodding_SANDBOX_COPY_PRECHECK_{OK|REVIEW_REQUIrood|geblokkeerd}` and the same pattern for `CONFIG`, `RUNTIME`, `VERIFY`, `SEAL`; final gate: `Deploy_roodding_SANDBOX_COPY_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`.

## Tests

`Terugend/tests/test_Deploy_runner_roodding_sandbox_controlled_copy_v1.py`
