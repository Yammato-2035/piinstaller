# Rescue — Runtime Assembly Pipeline (Strict)

## Kurzbeschreibung

Die Runtime-Assembly legt unter `build/rescue/runtime/` eine konsistente Verzeichnisstruktur (inkl. `boot/`, `EFI/`, `live/`), Backend-/Frontend-/Recovery-Manifeste, Offline-Konfig-JSON und **nur** Template-Skripte unter `runtime/scripts/`. Keine ISO, keine VM, kein privilegierter Host-Start.

## Artefakte

| Pfad | Rolle |
|------|--------|
| `build/rescue/runtime/runtime_root_manifest.json` | Erwartete Pfade + Platzhalterliste |
| `build/rescue/runtime/backend_runtime_assembly.json` | Uvicorn-Hinweis, Route-Checks |
| `build/rescue/runtime/frontend_runtime_assembly.json` | `frontend/dist`, Legacy in Assets / InspectRun |
| `build/rescue/runtime/recovery_runtime_assembly.json` | Rescue-/Verify-/Preview-/Inspect-Module, Evidence-Pfade |
| `build/rescue/runtime/offline_configuration_assembly.json` | Readonly/Offline/No-Cloud |
| `build/rescue/runtime/startup_script_assembly.json` | Liste geschriebener Template-Skripte |
| `docs/evidence/.../rescue_runtime_assembly_safety.json` | Routen-/Skript-Safety |
| `docs/evidence/.../rescue_runtime_assembly_final_gate.json` | Aggregiertes Gate |

## Verwandt

- `docs/deploy/DEPLOY_RESCUE_RUNTIME_ASSEMBLY_PIPELINE_DE.md` / `_EN.md`
- Runner: `backend/deploy/runner_rescue_runtime_assembly_pipeline.py`
