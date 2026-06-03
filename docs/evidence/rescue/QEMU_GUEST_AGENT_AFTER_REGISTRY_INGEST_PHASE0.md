# QEMU Guest Agent Smoke After Port Registry — Phase 0

**Datum:** 2026-06-03  
**Ingest:** Auswertung Operator-Lauf (kein neuer QEMU)  
**HEAD (Smoke):** `77253b5`  
**Branch:** `main`

## Runtime nach Release-Trap

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |

Artefakt: `qemu_guest_agent_after_registry_runtime_baseline_latest.json`

## QEMU-Run

| Feld | Wert |
|------|------|
| `run_id` | `qemu_rescue_developer_autopilot_20260603_111427` |
| `run_dir` | `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_autopilot_20260603_111427` |
| `run_dir` vorhanden | **yes** |

## Vor-QEMU (Operator-Log)

- `local_lab` aktiv
- `DEVSERVER_PREFLIGHT_OK`: fleet/dashboard HTTP 200
- Port-Registry/Preflight grün (siehe vorheriger Ingest `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md`)

## Nicht-Ziele (eingehalten)

Kein neuer QEMU · Kein ISO-Build · Kein USB/dd · Kein Backup/Restore · Kein Deploy
