# Version 1.7.3.0 — Acceptance

**Date:** 2026-05-30  
**Version bump commit:** 17c351a  
**Evidence commit:** 89ae576  
**Re-verification:** 2026-05-31 — deploy complete, gates OK, schema validated  
**HEAD:** 8aebf99  

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

## Deploy

| Step | Result |
|------|--------|
| `sudo ./scripts/deploy-to-opt.sh` | **completed** |
| Backend restart | performed |
| Web-UI restart | performed |
| Pakete gebaut | SetupHelfer_1.7.3_amd64.deb, SetupHelfer-1.7.3-1.x86_64.rpm, SetupHelfer_1.7.3_amd64.AppImage |

## Runtime (2026-05-31)

| Check | Result |
|-------|--------|
| Runtime-Gate | Exit **0** (OK) |
| Version-Gate | Exit **0** (OK) |
| `/api/version` | project_version=**1.7.3.0**, version=1.7.3.0 |
| `/api/dev-dashboard/control-center-summary` | **HTTP 200** — all sections under `.summary` |
| Dev-Server health | enabled=true, local_lab, storage_ok=true |
| Dev-Server summary | node_count=2, reports_last_24h=2 |
| Public uploads | disabled |
| SSH | disabled |

### Summary sections verified (`.summary | keys`)

runtime, roadmap, dev_server, rescue_developer, documentation, diagnostics, evidence, next_prompts, warnings, errors

### Schema note

Sections live under `.summary.*`, not top-level. Smoke `jq '.runtime, .roadmap, .dev_server'` returns null — expected wrapper schema.

See: `docs/evidence/dev-dashboard/CONTROL_CENTER_SUMMARY_SCHEMA_VALIDATION.md`

## Dirty Deploy Audit

| Check | Result |
|-------|--------|
| WIP files in `/opt` (SHA256 match) | **22** (16 modified + 4 untracked critical) |
| Manifest-Kern-Drift | green |
| ISO Dry-Build freigegeben | **NEIN** |

See: `docs/evidence/runtime-results/deploy/DIRTY_DEPLOY_AUDIT_1_7_3_0.md`

## Safety

No ISO, backup, restore, SSH, apt. No safety gates weakened.

## Status

| Area | Status |
|------|--------|
| Version bump (code) | **GREEN** |
| Control Center Summary API | **GREEN** (HTTP 200, schema OK) |
| Runtime version alignment | **GREEN** |
| Runtime-Gate | **GREEN** |
| Dirty Deploy (ISO-relevant) | **YELLOW/BLOCKING** |
| Overall runtime acceptance | **YELLOW** — clean redeploy vor ISO |

## Next prompt

**FIX CONTROL CENTER SUMMARY SCHEMA / CLEAN DIRTY RUNTIME DEPLOY**

(WIP stashen/committen → clean redeploy → dann ISO Dry-Build)

After clean redeploy + version gate OK:

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**
