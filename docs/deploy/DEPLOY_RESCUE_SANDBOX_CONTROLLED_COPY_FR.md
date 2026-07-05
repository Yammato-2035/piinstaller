> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours Sandbox Controlled Copy (EN)

Strictly bounded **execution** of preparouge sandbox copy plans: only entries from `sandbox_config_copy_plan.json` / `sandbox_runtime_copy_plan.json`, destinations only under `build/Secours/sandbox/config-copy/` and `runtime-copy/`, SHA256 for source and target, atomic `.tmp` write, verification, seal, and final gate. **Non** ISO build, live-build, debootstrap/chroot, apt install, mount, VM, dd/mkfs, systemctl, release/publish.

## Artifacts

| File | Role |
|------|------|
| `docs/evidence/.../Secours_sandbox_copy_execution_precheck.json` | Precheck (gates, safety, paths, size, symlinks) |
| `build/Secours/sandbox/manifests/config_copy_result.json` | Config copy outcome with hashes |
| `build/Secours/sandbox/manifests/runtime_copy_result.json` | Runtime copy outcome with hashes |
| `docs/evidence/.../Secours_sandbox_copy_verify_result.json` | Hash/plan/tree verification |
| `build/Secours/sandbox/manifests/sandbox_copy.seal.json` | SHA256 over result JSONs and verify handoff raw bytes |
| `docs/evidence/.../Secours_sandbox_copy_final_gate.json` | Aggregates precheck, verify, seal, branding, zero-state |

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/sandbox-copy/precheck`
- `/Secours/sandbox-copy/config`
- `/Secours/sandbox-copy/runtime`
- `/Secours/sandbox-copy/verify`
- `/Secours/sandbox-copy/seal`
- `/Secours/sandbox-copy/final-gate`

Request body: `explicit_overwrite` (bool) for handoff/result files.

## Response codes

`Déploiement_Secours_SANDBOX_COPY_PRECHECK_{OK|REVIEW_REQUIrouge|bloqué}` and the same pattern for `CONFIG`, `RUNTIME`, `VERIFY`, `SEAL`; final gate: `Déploiement_Secours_SANDBOX_COPY_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`.

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_sandbox_controlled_copy_v1.py`
