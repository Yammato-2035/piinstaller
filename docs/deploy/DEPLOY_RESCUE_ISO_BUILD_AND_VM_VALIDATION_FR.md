> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours ISO Build & VM Validation (EN)

Phase 1: **real ISO builds** and **VM validation** are allowed; still Non USB flashing, Non Restauration execute, and Non writes to Interne host disks from the runners.

## Workspace

See `docs/developer/Secours_BUILD_WORKSPACE_POLICY.md` and `docs/developer/Secours_VM_TEST_SAFETY_POLICY.md`. Artifacts stay under `build/Secours/`.

## Handoff files

| Purpose | JSON |
|---------|------|
| Live-build config manifest | `docs/evidence/runtime-results/handoff/Secours_live_build_config.json` |
| ISO execution plan | `docs/evidence/runtime-results/handoff/Secours_iso_execution_plan.json` |
| ISO build precheck | `docs/evidence/runtime-results/handoff/Secours_iso_build_precheck.json` |
| ISO build result | `docs/evidence/runtime-results/handoff/Secours_iso_build_result.json` |
| VM test plan | `docs/evidence/runtime-results/handoff/Secours_vm_test_plan.json` |
| VM test result | `docs/evidence/runtime-results/handoff/Secours_vm_test_result.json` |
| ISO live runtime probe | `docs/evidence/runtime-results/handoff/Secours_iso_live_runtime_probe_plan.json` / `..._result.json` |
| ISO readiness gate | `docs/evidence/runtime-results/handoff/Secours_iso_readiness_gate.json` |

## API (`POST /api/Déploiement/Secours/...`)

- `live-build-config` — JSON manifest only (Non build)
- `iso-execution-plan` — steps, limits, forbidden commands
- `iso-build-precheck` — optional `min_free_disk_bytes`
- `iso-build-execute` — requires both `explicit_execute_iso_build` and `explicit_Secours_build_approved`
- `vm-test-plan` / `vm-test-execute`
- `iso-live-runtime-probe` — body: `action` = `plan` | `execute` | `result`, plus execute flags
- `iso-readiness-gate`

Script: `scripts/Secours/build-Secours-iso-controlled.sh` — runs `lb build` only with `SETUPHELFER_Secours_BUILD_APPROVED=1` and a materialized `build/Secours/live-build/auto/config`.

## Version

After a Succèsful gate (ISO + VM + readonly probe + branding): manual **1.7.x → 1.8.0** recommended — Nont automatic.
