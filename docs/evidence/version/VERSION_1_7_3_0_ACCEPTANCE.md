# Version 1.7.3.0 — Acceptance

**Date:** 2026-05-30
**Version bump commit:** 17c351a
**Evidence commit:** 89ae576
**Re-verification:** 2026-05-30 — summary HTTP 200 confirmed; `/api/version` still 1.7.2 until redeploy

## Version bump

| Field | Value |
|-------|-------|
| Previous | 1.7.2 |
| New | **1.7.3.0** |
| Tauri/Cargo Semver | 1.7.3 (derived via `sync-version.js`) |

### Changed files

- `config/version.json` (canonical)
- `VERSION`
- `frontend/package.json`
- `frontend/src-tauri/tauri.conf.json`
- `frontend/src-tauri/Cargo.toml`
- `package.json` (root)
- `CHANGELOG.md`

## Tests (pre-deploy)

| Suite | Result |
|-------|--------|
| `test_dev_control_center_*` | 9 OK |
| `test_devserver_*` | 98 OK, 7 skipped |
| `test_devserver_agent_*` | 54 OK |
| ControlCenterOverview (frontend) | 4 OK |
| DevelopmentServerPanel (frontend) | 4 OK |

## Deploy (this run)

| Step | Result |
|------|--------|
| `sudo ./scripts/deploy-to-opt.sh` | **blocked** — `runtime_deploy_blocked_operator_sudo_required` |
| Backend restart | not performed |
| Web-UI restart | not performed |

## Runtime (after version commit, before operator redeploy)

| Check | Result |
|-------|--------|
| Runtime-Gate | Exit **12** (deploy drift — workspace 1.7.3.0 vs runtime 1.7.2) |
| Version-Gate | Exit **14** (workspace/api mismatch) |
| `/api/version` | project_version=**1.7.2** (runtime not yet updated) |
| `/api/dev-dashboard/control-center-summary` | **HTTP 200** — all sections present |
| Dev-Server health | enabled=true, local_lab, storage_ok=true |
| Dev-Server summary | node_count=2, reports_last_24h=2 |
| Public uploads | disabled |
| SSH | disabled |

### Summary sections verified

runtime, roadmap, dev_server, rescue_developer, documentation, diagnostics, evidence, next_prompts, warnings, errors

## Operator redeploy required

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
./scripts/check-runtime-deploy-gate.sh
./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

Expected after redeploy: `project_version=1.7.3.0`, gates OK.

## Safety

No ISO, backup, restore, SSH, apt. No safety gates weakened.

## Status

| Area | Status |
|------|--------|
| Version bump (code) | **GREEN** |
| Control Center Summary API | **GREEN** (live HTTP 200) |
| Runtime version alignment | **YELLOW** — deploy required |
| Overall runtime acceptance | **YELLOW** |

## Next prompt

After operator redeploy + version gate OK:

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**

Until then:

**FIX VERSION / CONTROL CENTER RUNTIME DEPLOY DRIFT**
