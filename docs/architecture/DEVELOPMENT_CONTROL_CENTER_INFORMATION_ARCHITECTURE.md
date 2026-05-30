# Development Control Center — Information Architecture

## 1. Header: overall state

- Runtime gate (from `scripts/check-runtime-deploy-gate.sh` signals via dashboard)
- Deploy drift
- Version / backend path
- Safe-test mode
- Open blockers (never hidden)

## 2. Roadmap

- Current phase / overall status
- Green / yellow / red / gray areas (evidence-based)
- Recommended next prompt
- Blocked tasks
- Recent milestones

Source: `docs/roadmap/setuphelfer_roadmap.json` via `/api/dev-dashboard/roadmap`

## 3. Development Server (telemetry)

- enabled, mode, storage_ok
- node_count, online_count, reports_last_24h
- latest_findings, agent last report
- ssh_allowed — **disabled is correct in lab MVP**
- public_uploads_allowed — **disabled is correct**

## 4. Rescue developer pipeline

| Item | Status rule |
|------|-------------|
| Dev Server MVP | green with evidence file |
| Dev Agent MVP | green with evidence file |
| Rescue Developer Profile | green with integration evidence |
| Public Profile Guard | green when validation passes |
| ISO Dry-Build | **pending** until real build evidence |

## 5. Documentation / FAQ / KB

Read-only counts from `docs/`:
- total md, faq, kb, architecture, runbooks, evidence
- DE/EN pair completeness
- missing counterpart list

## 6. Diagnostics

- Catalog from `core.diagnostics.registry`
- Test file count (`test*diagnostic*`)
- KB articles under `docs/knowledge-base/diagnostics/`

## 7. Evidence

- Recent files from evidence index
- Buckets: dev-server, rescue, release-gates, runtime-results

## 8. Actions / prompts

- Recommended prompt from roadmap registry
- Rescue pipeline next step
- **No dangerous actions** from UI (backup, restore, ISO build, SSH)

## API

`GET /api/dev-dashboard/control-center-summary` — read-only aggregate.

## Status colors

| Color | Meaning |
|-------|---------|
| green | Evidence or API confirms OK |
| yellow | pending / review / gaps |
| red | failed / blocked |
| gray | unknown / not_available |
