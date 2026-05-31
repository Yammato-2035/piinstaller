# Control Center Overview Improvement — Evidence

**Date:** 2026-05-30  
**Feature commit:** 4b85bd2  
**Version bump commit:** 17c351a (1.7.3.0)  
**Evidence commit:** 89ae576  
**Schema validation:** 2026-05-31 (HEAD 8aebf99)  
**Branch:** main  

## Runtime acceptance summary

| Check | Result |
|-------|--------|
| Deploy 1.7.3.0 | **yes** — operator redeploy completed |
| Backend restart | **yes** |
| Runtime-Gate | Exit **0** (OK) |
| Version-Gate | Exit **0** (OK) |
| `/api/version` | project_version=**1.7.3.0** |

## Control Center Summary API

| Field | Value |
|-------|-------|
| HTTP status | **200** |
| Top-Level-Keys | `status`, `summary` |
| Sektionen unter | `.summary.*` (nicht Top-Level) |
| Sections | runtime, roadmap, dev_server, rescue_developer, documentation, diagnostics, evidence, next_prompts, warnings, errors |

**Schema-Entscheidung (2026-05-31):** Fall A — Smoke-Kommando war falsch. Backend liefert korrekt `{ status, summary }`. Frontend nutzt `data.summary`. Keine Codeänderung.

Siehe: `docs/evidence/dev-dashboard/CONTROL_CENTER_SUMMARY_SCHEMA_VALIDATION.md`

## Dev-Server (live)

| Field | Value |
|-------|-------|
| enabled | true |
| mode | local_lab |
| storage_ok | true |
| ssh_allowed | false |
| public_uploads_allowed | false |
| node_count | 2 |
| reports_last_24h | 2 |

## `/api/version` (live)

- project_version: **1.7.3.0**
- backend_runtime_path: `/opt/setuphelfer/backend`

## Version 1.7.3.0

- Canonical: `config/version.json` → `1.7.3.0`
- Sync: `frontend/sync-version.js` → package.json, Tauri 1.7.3, VERSION
- See: `docs/evidence/version/VERSION_1_7_3_0_ACCEPTANCE.md`

## Tests

| Suite | Result |
|-------|--------|
| Backend control center | 9 OK |
| Backend devserver | 98 OK, 7 skipped |
| Backend devserver agent | 54 OK |
| Frontend ControlCenterOverview | 4 OK |
| Frontend DevelopmentServerPanel | 4 OK |

## Dirty Deploy Audit

Runtime enthält uncommitted WIP (22 SHA256-Matches). ISO Dry-Build **blockiert**.

Siehe: `docs/evidence/runtime-results/deploy/DIRTY_DEPLOY_AUDIT_1_7_3_0.md`

## Safety

- No ISO, backup, restore, SSH, apt
- Public uploads disabled (correct)
- SSH disabled (correct)
- ISO dry-build status remains pending (no fake green)

## Status rules

| Area | Status |
|------|--------|
| Control Center Summary live | **GREEN** |
| Summary-Schema | **GREEN** (Smoke korrigiert) |
| Runtime version 1.7.3.0 | **GREEN** |
| Runtime-Gate full green | **GREEN** |
| Dirty Deploy (ISO-relevant) | **YELLOW/BLOCKING** |

## Korrekter Smoke-Befehl

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.summary | keys'
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.summary.runtime, .summary.roadmap, .summary.dev_server'
./scripts/check-runtime-deploy-gate.sh && ./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

## Next prompt

**FIX CONTROL CENTER SUMMARY SCHEMA / CLEAN DIRTY RUNTIME DEPLOY**

Vor ISO-Dry-Build: WIP stashen oder committen, dann clean redeploy.

Nach clean redeploy + Gates OK:

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**
