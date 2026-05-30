# Development Server MVP — Runtime Acceptance (FINAL)

**Date:** 2026-05-30
**Commit:** `806ce08` — Add setuphelfer development server MVP
**Version:** 1.7.2
**Branch:** `main`

## Summary

| Area | Status |
|------|--------|
| Runtime gate | **GREEN** — `check-runtime-deploy-gate: OK` |
| OpenAPI `/api/dev-server/*` | **GREEN** — routes visible |
| Health | **GREEN** — enabled=true, mode=local_lab, storage_ok=true |
| Local ingest smoke | **GREEN** — DEV_SERVER_REPORT_ACCEPTED |
| Nodes / Summary | **GREEN** — local-smoke-node, reports_last_24h=1 |
| SSH-blocked smoke | **GREEN** — DEV_SERVER_SSH_ACTION_BLOCKED, ssh_not_allowed |
| Public uploads | **disabled** — public_uploads_allowed=false |
| SSH | **disabled** — ssh_allowed=false |
| Write/backup/restore/repair routes | **absent** |
| Agent | **pending** (this acceptance predates agent MVP) |

## Health (live)

```json
{
  "enabled": true,
  "mode": "local_lab",
  "storage_ok": true,
  "ssh_allowed": false,
  "public_uploads_allowed": false,
  "version": "1.7.2"
}
```

## Local ingest smoke

- **code:** DEV_SERVER_REPORT_ACCEPTED
- **node_id:** local-smoke-node
- **report_id:** local-smoke-report
- **redaction_status:** raw_lab
- **summary:** node_count=1, reports_last_24h=1

## SSH-blocked smoke

- **code:** DEV_SERVER_SSH_ACTION_BLOCKED
- **errors:** `["ssh_not_allowed"]`

## Storage / audit paths

- Workspace/runtime: `docs/evidence/runtime-results/dev-server/`
- Subdirs: `nodes/`, `reports/`, `actions/`, `latest/`, `audit/dev_server_events.jsonl`

## Systemd dev-server lab config

Drop-in: `/etc/systemd/system/setuphelfer-backend.service.d/90-devserver-local-lab.conf`

- SETUPHELFER_DEV_SERVER_ENABLED=true
- SETUPHELFER_DEV_SERVER_MODE=local_lab
- SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=false
- SETUPHELFER_DEV_SERVER_ACCEPT_PUBLIC_UPLOADS=false
- SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN=false

## Security

- No public auto-upload
- No free shell on dev-server SSH (disabled)
- No backup/restore/repair dev-server routes
- No secrets in repo

## Next

Development Server Agent for Rescue Developer Edition (separate MVP commit).
