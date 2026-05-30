# Control Center Overview — Gap Analysis

**Date:** 2026-05-30
**HEAD:** 8e07acf (start of this run)

## Current UI structure

| Component | Location | Role |
|-----------|----------|------|
| ExternalDevelopmentControlCenter | `frontend/src/pages/ExternalDevelopmentControlCenter.tsx` | Main cockpit page |
| RoadmapDrawer | `frontend/src/components/dev-dashboard/RoadmapDrawer.tsx` | Roadmap tree, prompts, diagnostics progress |
| DevelopmentServerPanel | `frontend/src/components/devserver/DevelopmentServerPanel.tsx` | Dev-server health/nodes |
| Governance matrix | via `useGovernanceMonitor` | 16-area traffic lights |
| Many operation panels | RescueStickBoard, DeployStatus, Backup, etc. | Stacked below roadmap |

## Problems identified

1. **Overview overload** — Roadmap, rescue boards, deploy, notifications, dev-server and backup panels stacked vertically; roadmap scrolls out of view.
2. **Roadmap visibility** — Roadmap data exists via `/api/dev-dashboard/roadmap` and is merged in `loadDevDashboard.ts`, but buried under operational panels.
3. **Telemetry** — DevelopmentServerPanel existed but lacked storage/public-upload/agent context and was not grouped.
4. **Doc/KB/Diagnostics** — `DocsConsistencyPanel` minimal; no FAQ/KB counts or translation-pair gaps.
5. **Rescue/Agent pipeline** — No dedicated status for Dev Server MVP → Agent → Developer Profile → ISO pending.
6. **No unified summary API** — Frontend fetched status, modules, evidence, roadmap separately.

## Available API data (before this run)

| Endpoint | Data |
|----------|------|
| `/api/dev-dashboard/status` | Runtime gate, deploy drift, roadmap embedded |
| `/api/dev-dashboard/roadmap/*` | Full registry bundle |
| `/api/dev-server/health` | enabled, mode, storage, ssh, public uploads |
| `/api/dev-server/summary` | nodes, reports, findings |
| `/api/dev-dashboard/evidence-index` | Evidence file buckets |

## Missing API data (before this run)

- Unified `control-center-summary`
- Documentation/FAQ/KB counts
- Translation-pair gap list
- Rescue developer pipeline status
- Agent last-report in dashboard context

## Proposed structure (implemented)

1. Tabbed sections: Overview, Roadmap, Telemetry, Rescue/Agent, Docs & Diagnostics, Evidence, Operations
2. `GET /api/dev-dashboard/control-center-summary` read-only aggregator
3. Compact overview header with blockers and next prompt
4. No fake green — ISO build stays `pending`

## Risks

- Summary endpoint requires backend deploy to runtime for live smoke
- Documentation counts are filesystem scans — may be slow on large trees (capped)
- Roadmap still depends on registry JSON validity

## Open questions

- SSE/WebSocket live refresh for summary
- Finer documentation coverage metrics
- Integrate summary into Tauri standalone mode

**No implementation success claimed in this scan document.**
