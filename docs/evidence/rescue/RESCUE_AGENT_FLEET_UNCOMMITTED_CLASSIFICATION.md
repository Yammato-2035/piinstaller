# Uncommitted — Klassifikation (Rescue Agent / Fleet Commit)

**Stand:** 2026-06-02

## Gruppe A — commit_candidate (dieser Commit)

| Datei / Muster | Status | Grund | Commit |
|----------------|--------|-------|--------|
| `backend/rescue_agent/**` | commit_candidate | Contract-Stubs | ja |
| `backend/core/fleet_session_state.py` | commit_candidate | Heartbeat `running` → `agent_state` | ja |
| `backend/core/install_profile.py` | commit_candidate | `/api/rescue-agent` Gating | ja |
| `backend/fleet/schemas.py` | commit_candidate | `agent_state` Feld | ja |
| `backend/tests/test_fleet_session_heartbeat_payload_v1.py` | commit_candidate | Regression | ja |
| `backend/tests/test_rescue_agent_*_v1.py` | commit_candidate | Contract-Tests | ja |
| `scripts/rescue-live/fleet-session-api.sh` | commit_candidate | Script neutralisiert `status=running` | ja |
| `frontend/.../fleetSessionsApi.ts` | commit_candidate | API + 404-safe fetch | ja |
| `frontend/.../RescueAgentPanel.tsx` | commit_candidate | DCC-Stub | ja |
| `frontend/.../LabSessionsPanel.tsx` | commit_candidate | Panel-Einbindung | ja |
| `frontend/.../rescue/RescueLiveSetupMenu.tsx` | commit_candidate | Live-Menü-Stub | ja |
| `docs/architecture/RESCUE_*.md` (5) | commit_candidate | Architektur | ja |
| `docs/dev-dashboard/RESCUE_AGENT_DASHBOARD.md` | commit_candidate | Doku | ja |
| `docs/rescue-stick/RESCUE_LIVE_SETUP_MENU.md` | commit_candidate | Doku | ja |
| `docs/knowledge-base/rescue/RESCUE_AGENT_AND_DEVSERVER.md` | commit_candidate | KB | ja |
| `docs/faq/RESCUE_STICK_FAQ_{DE,EN}.md` | commit_candidate | FAQ | ja |
| Evidence rescue/dev-dashboard (siehe Phase 8 `git add`) | commit_candidate | Abnahme | ja |
| `docs/roadmap/STATUS_MATRIX.md`, `CHANGELOG.md` | commit_candidate | Status | ja |

## Gruppe B — exclude

| Datei / Muster | Status | Grund | Commit |
|----------------|--------|-------|--------|
| `build/rescue/**` | exclude_build_artifact | Live-Build-Tree | nein |
| `docs/evidence/runtime-results/rescue/qemu/**` | exclude_runtime_artifact | QEMU-Läufe | nein |
| `*.iso`, `*.img`, `*.qcow2`, `*.partial` | exclude_runtime_artifact | Binär | nein |
| `.cursor/rules/**` | exclude_local_tooling | Editor, nicht freigegeben | nein |
| `frontend/public/dev-dashboard.snapshot.json` | exclude_local_tooling | Snapshot | nein |
| `typescript` (root) | exclude_local_tooling | Artefakt | nein |
| `backend/core/rescue_iso_build_logs.py` | unrelated_existing_change | ISO-Executor, anderer Scope | nein |
| `packaging/**`, `ckb-next` | unrelated_existing_change | nicht Rescue-Agent | nein |
| Lab-Acceptance JSON, handoff manifests | unrelated_existing_change | separater Lauf | nein |
| `frontend/.../Documentation.tsx`, `RaspberryPiConfig.tsx` | unrelated_existing_change | nicht Panel-Scope | nein |

## Gruppe C — review_required

| Datei | Status | Grund | Commit |
|-------|--------|-------|--------|
| `docs/evidence/dev-dashboard/DCC_*` | review_required | Deploy-Drift-Analyse; optional separat | nein (dieser Commit) |
| `RescueBuildLogPanel.tsx` | review_required | ISO-Build-UI, nicht in Pflichtliste | nein |
