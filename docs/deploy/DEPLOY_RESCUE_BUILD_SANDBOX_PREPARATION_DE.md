# Deploy — Rescue Build Sandbox Preparation (DE)

Read-only **Sandbox-Vorbereitung** unter `build/rescue/sandbox/` fuer spaetere Debian-Live-Testbuilds: Verzeichnisstruktur, **Plaene** fuer Config-/Runtime-Kopien (ohne binaere Massenkopie), Overlay-Pfade (ohne Mount), Cleanup-/Rollback-Metadaten, Safety- und Final-Gate.

## Verbote in dieser Phase

Kein echter Build, kein `lb build`, kein `debootstrap`, kein Chroot, kein ISO, kein SquashFS-Tooling, kein `grub-mkrescue`, kein `xorriso`, kein `apt install`, kein VM-Boot, keine `subprocess`-/`mount(`-Aufrufe im Runner.

## Artefakte

| Datei | Rolle |
|-------|--------|
| `build/rescue/sandbox_root_manifest.json` | Wurzel, erlaubte Schreibpfade, Readonly-Hinweise |
| `build/rescue/sandbox_config_copy_plan.json` | Text/Manifest-Ziele unter `sandbox/config-copy/` |
| `build/rescue/sandbox_runtime_copy_plan.json` | Runtime-Textdateien; blockiert u. a. `.iso`/`.img`/`.qcow2`, `node_modules`, `.git` |
| `build/rescue/overlay_workspace_plan.json` | `lowerdir`/`upperdir`/`workdir` — nur Planung |
| `build/rescue/build_cleanup_plan.json` | Cleanup-Reihenfolge, `destructive_cleanup: false` |
| `docs/evidence/.../rescue_build_sandbox_safety.json` | Safety-Handoff |
| `docs/evidence/.../rescue_build_sandbox_final_gate.json` | Final-Gate |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/build-sandbox/root`
- `/rescue/build-sandbox/config-copy-plan`
- `/rescue/build-sandbox/runtime-copy-plan`
- `/rescue/build-sandbox/overlay-workspace-plan`
- `/rescue/build-sandbox/cleanup-plan`
- `/rescue/build-sandbox/safety-validation`
- `/rescue/build-sandbox/final-gate`

## Response-Codes

`DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_{OK|REVIEW_REQUIRED|BLOCKED}` usw. sowie `DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_build_sandbox_preparation_v1.py`
