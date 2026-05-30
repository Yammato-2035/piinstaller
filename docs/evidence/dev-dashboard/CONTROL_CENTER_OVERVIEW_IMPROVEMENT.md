# Control Center Overview Improvement — Evidence

**Date:** 2026-05-30
**HEAD start:** 8e07acf
**HEAD end:** (pending commit)
**Branch:** main
**Runtime gate:** OK

## Runtime smoke

| Check | Result |
|-------|--------|
| `/api/dev-dashboard/status` | OK (live) |
| `/api/dev-server/health` | enabled=true, local_lab, storage_ok=true |
| `/api/dev-server/summary` | node_count=2, reports_last_24h=2 |
| `/api/dev-dashboard/control-center-summary` | **404 — runtime_deploy_or_restart_required** |

Local workspace test of aggregator: **OK** (Python direct call).

## Changes

### Backend
- `backend/core/dev_control_center_summary.py` — read-only aggregator
- `backend/app.py` — `GET /api/dev-dashboard/control-center-summary`
- `backend/tests/test_dev_control_center_summary_v1.py` — 9 tests OK

### Frontend
- Tabbed `ExternalDevelopmentControlCenter`
- `ControlCenterOverviewHeader`, `DocumentationDiagnosticsCard`, `RescueDeveloperPipelineCard`, `ControlCenterSectionTabs`
- Enhanced `DevelopmentServerPanelView` (storage, SSH/public safe states, latest findings)
- `frontend/src/api/devDashboardApi.ts`

### Docs
- Gap analysis, architecture, overview DE/EN, FAQ DE/EN, KB entry

## Feature status

| Feature | Status |
|---------|--------|
| Roadmap visible (tab) | yes |
| Telemetry server visible | yes |
| Doc/FAQ/KB/diagnostics stats | yes |
| Rescue/Agent pipeline card | yes |
| Backend tests | 9 OK |
| Frontend tests | ControlCenterOverview 4 OK, DevelopmentServerPanel 4 OK |
| Runtime summary API live | **deploy_required** |

## Safety

- No ISO build, USB write, backup, restore, SSH, apt
- Public uploads disabled unchanged
- No fake green for ISO build

## Open points

- Deploy backend + frontend for live summary smoke
- Roadmap data quality refinements
- SSE/WebSocket refresh
- Rescue ISO dry-build (next prompt)

## Next prompt

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD** (after deploy)
