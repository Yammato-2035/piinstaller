# Developer QEMU Profile Fix — Phase 0 Baseline

**Datum:** 2026-06-02  
**Auftrag:** STRICT MODE — Fix Developer QEMU ISO Profile (Serial + Agent Autostart)

## Git / Repo

| Feld | Wert |
|------|------|
| **HEAD (vor Fix)** | `664bdca` |
| **Branch** | `main` |
| **Commit-Messages (Kontext)** | Operator-QEMU-Smoke-Ingest blocked; Controlled ISO Build LB_EXIT=0 (Standard-Profil) |

## Runtime (readonly)

| Feld | Wert |
|------|------|
| `setuphelfer-backend.service` | active |
| `install_profile` | release |
| `profile_gate_status` | green |
| `dev_control_enabled` | false |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |

## QEMU-Smoke-Status vorher

| Feld | Wert |
|------|------|
| Run-ID | `qemu_rescue_developer_autopilot_20260602_202725` |
| QEMU gestartet | yes |
| QEMU Exit | 124 (timeout) |
| Serial size | 0 Bytes |
| Autopilot status | failed |
| `guest_found` | false |
| `report_new` | false |
| Fleet Session | vorhanden, final `timeout` |
| Findings | `serial_empty`, `qemu_timeout_124`, `guest_report_missing` |
| Rescue-Agent Session | no |
| dev_server reports | 0 → 0 |

## Root Cause vorher

| Klasse | Beschreibung |
|--------|--------------|
| **primary** | `qemu_serial_capture_failure` |
| **secondary** | `guest_agent_autostart_gap` |
| **additional** | Profil-Mismatch Standard-ISO vs Developer-QEMU-Autopilot-Smoke |

**Kernbefund:** Controlled ISO Build lief mit `rescue_build_profile=standard` (`quiet splash`, kein `console=ttyS0`). Autopilot-Unit im Squashfs vorhanden, aber nicht enabled. QEMU-Smoke gegen Standard-ISO ausgeführt.

## Bewertung

**fix_required:** `true`

Evidence: `docs/evidence/rescue/QEMU_GUEST_AGENT_FAILURE_CLASSIFICATION.md`, `docs/evidence/rescue/qemu_guest_agent_smoke_latest.json`
