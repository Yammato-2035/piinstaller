# Control Center Overview Improvement — Evidence

**Date:** 2026-05-30
**Feature commit:** 4b85bd2
**Version bump commit:** 17c351a (1.7.3.0)
**Evidence commit:** (pending)
**Branch:** main

## Runtime acceptance summary

| Check | Result |
|-------|--------|
| Deploy (this run) | **no** — sudo blocked |
| Backend restart (this run) | **no** |
| Web-UI restart (this run) | **no** |
| Prior manual deploy (4b85bd2) | **yes** — summary endpoint live |
| Runtime-Gate (2026-05-30 post-bump) | Exit **12** (version drift 1.7.3.0 workspace vs 1.7.2 runtime) |
| Version-Gate | Exit **14** (api=1.7.2, workspace=1.7.3.0) |

## Control Center Summary API

| Field | Value |
|-------|-------|
| HTTP status | **200** |
| OpenAPI registered | yes |
| Sections | runtime, roadmap, dev_server, rescue_developer, documentation, diagnostics, evidence, next_prompts, warnings, errors |

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

- project_version: **1.7.2** (until operator redeploy of 17c351a)
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

## Frontend runtime smoke

**pending** — Web-UI not HTTP-verified this run.

## Safety

- No ISO, backup, restore, SSH, apt
- Public uploads disabled (correct)
- SSH disabled (correct)
- ISO dry-build status remains pending (no fake green)

## Status rules

| Area | Status |
|------|--------|
| Control Center Summary live | **GREEN** |
| Runtime version 1.7.3.0 | **YELLOW** — operator redeploy required |
| Runtime-Gate full green | **YELLOW** |

## Operator next step

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
./scripts/check-runtime-deploy-gate.sh && ./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.summary | keys'
```

## Next prompt

After redeploy + gates OK:

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**

Until redeploy:

**FIX VERSION / CONTROL CENTER RUNTIME DEPLOY DRIFT**
