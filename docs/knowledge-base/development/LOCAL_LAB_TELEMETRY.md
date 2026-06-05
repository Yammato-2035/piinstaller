# Local Lab Telemetry

## Overview

Lab telemetry collects structured reports from developer-owned test systems **only** when the Development Server is enabled in `local_lab` mode.

**Rescue-Stick-Telemetrie** (Windows Inspect, Release-tauglich) nutzt einen **separaten** Kanal — siehe `docs/knowledge-base/development/RESCUE_TELEMETRY_INGEST.md` (`/api/rescue/telemetry/*`, nicht DCC).

## Data flow

1. Rescue stick developer edition or lab agent sends `POST /api/dev-server/ingest/report`
2. Node registry is created/updated
3. Report stored under `docs/evidence/runtime-results/dev-server/reports/`
4. Audit event appended to `audit/dev_server_events.jsonl`
5. Dashboard panel shows node status

## Lab mode rules

- **local_lab**: raw payload allowed (`redaction_status: raw_lab`)
- **beta_opt_in**: payload redacted before storage
- **public_rescue**: auto-upload blocked unless `SETUPHELFER_DEV_SERVER_ACCEPT_PUBLIC_UPLOADS=true`

## Sensitive fields

Redaction module hashes/removes hostname, username, MAC, disk serial, tokens, etc. See `backend/devserver/redaction.py`.

## Not collected in MVP

- User tracking
- Cloud upload
- Automatic repair actions
