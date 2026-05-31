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

Runtime HEAD-clean nach Clean Deploy (0 WIP-Matches). Siehe `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_1_7_3_0.md`.

## Rescue Developer ISO Dry-Build

| Field | Value |
|-------|-------|
| Executed | **2026-05-31** |
| Status | **review_required** (prior ISO artifacts only) |
| Agent Profile Guard | **OK** (exit 0) |
| Public Guard | **OK** |
| Real ISO built | **no** |
| Manifest | `docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest.json` |

## Safety

- No ISO, backup, restore, SSH, apt
- Public uploads disabled (correct)
- SSH disabled (correct)
- ISO dry-build executed — real ISO build remains **pending**

## Status rules

| Area | Status |
|------|--------|
| Control Center Summary live | **GREEN** |
| Summary-Schema | **GREEN** |
| Runtime version 1.7.3.0 | **GREEN** |
| Runtime-Gate full green | **GREEN** |
| Dirty Deploy (ISO-relevant) | **GREEN** |
| Rescue Developer ISO Dry-Build | **YELLOW** (review_required — prior artifacts) |

## Korrekter Smoke-Befehl

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.summary | keys'
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.summary.runtime, .summary.roadmap, .summary.dev_server'
./scripts/check-runtime-deploy-gate.sh && ./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
PYTHONPATH=backend:. python3 -m backend.devserver_agent.cli --rescue-iso-dry-build \
  --developer-profile-root build/rescue/profiles/developer \
  --public-profile-root build/rescue/profiles/public \
  --output docs/evidence/runtime-results/rescue/rescue_developer_iso_dry_build_manifest.json --json
```

## Rescue Developer Controlled ISO Build

| Field | Value |
|-------|-------|
| Run-ID | `rescue_developer_iso_20260531_095558` |
| Status | **blocked** (exit 30, no ISO) |
| Developer profile in build tree | **prepared** |
| Real ISO built | **no** |
| Blocker | operator sudo policy |

See: `docs/evidence/rescue/RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`

## Next prompt

**FIX RESCUE DEVELOPER CONTROLLED ISO BUILD** — operator terminal with sudo required.
