# Developer QEMU Rebuild Blocker — Phase 0

**Datum:** 2026-06-02  
**HEAD:** `488e1ad`  
**Branch:** `main`

## Runtime (readonly)

| Feld | Wert |
|------|------|
| `install_profile` | release |
| `profile_gate_status` | green |
| `dev_control_enabled` | false |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |

## Letzter Buildversuch

| Feld | Wert |
|------|------|
| run_id | `rescue_developer_iso_20260602_212524` |
| started_at | `2026-06-02T23:25:24+02:00` |
| LB_EXIT | **34** |
| Summary-Status | failed |
| error_code | `rescue_iso_build.permission_denied_dot_build` |
| build_started | false |
| Buildprofil laut Summary/Log | **standard** |

## Blocker

| Feld | Wert |
|------|------|
| root_owned_top_level_artifacts | yes (7) |
| root_owned_active_count | 0 |
| Samples | binary.contents, binary.packages, chroot.headers, chroot.packages.install, chroot.packages.live, wget-log, wget-log.1 |
| next_action (Summary) | `run_clean_controlled_live_build_tree` |

## Bewertung

| Flag | Wert |
|------|------|
| `rebuild_blocked_by_root_owned_top_level_artifacts` | **true** |
| `rebuild_profile_mismatch_detected` | **true** (Ziel developer-qemu, Versuch profile=standard) |

Evidence: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
