# Deploy — Rescue Build Environment Emulation (DE)

Read-only **Emulation** einer Debian-Live-Build-Umgebung fuer Setuphelfer Rescue: Zustands-Snapshot, simulierter Workspace, simulierte Outputs (nur Metadaten, `generated: false`), simulierte Build-Logs, Overlay-/Persistence-Emulation ohne Mount, Verify, Seal und Final-Gate.

## Verbote

Kein `lb build`, kein debootstrap, kein Chroot, kein `apt install`, kein SquashFS-Pack, kein `grub-mkrescue`, kein xorriso, kein ISO, kein `mount`, keine VM — nur JSON-Artefakte unter `build/rescue/emulation/` und Evidence-Handoffs.

## Artefakte

| Datei | Rolle |
|-------|--------|
| `build/rescue/emulation/build_environment_snapshot.json` | Sandbox-/Runtime-/Copy-Zustand, `no_real_build_execution` |
| `build/rescue/emulation/simulated_build_workspace.json` | Simulierter Dateibaum, Workdirs |
| `build/rescue/emulation/simulated_build_outputs.json` | Emulierte Artefakt-Metadaten |
| `build/rescue/emulation/simulated_build_logs.json` | Geordnete Stufen, simulierte Dauer |
| `build/rescue/emulation/overlay_persistence_emulation.json` | lower/upper/work, ohne Mount |
| `docs/evidence/.../rescue_build_emulation_verify.json` | Verify |
| `build/rescue/emulation/build_emulation.seal.json` | SHA256-Bundle |
| `docs/evidence/.../rescue_build_emulation_final_gate.json` | Final-Gate |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/build-emulation/environment-snapshot`
- `/rescue/build-emulation/workspace`
- `/rescue/build-emulation/outputs`
- `/rescue/build-emulation/logs`
- `/rescue/build-emulation/overlay`
- `/rescue/build-emulation/verify`
- `/rescue/build-emulation/seal`
- `/rescue/build-emulation/final-gate`

## Response-Codes

`DEPLOY_RESCUE_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_{OK|REVIEW_REQUIRED|BLOCKED}` usw.; Final-Gate: `DEPLOY_RESCUE_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_build_environment_emulation_v1.py`
