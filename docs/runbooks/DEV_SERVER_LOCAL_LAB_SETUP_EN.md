# Runbook: Development Server — Local Lab Setup (EN)

## Prerequisites

- Setuphelfer backend running locally (typically port 8000)
- **Own** lab hardware / VMs only
- No public rescue auto-upload

## Steps

1. Set token (local, do not commit):

   ```bash
   export SETUPHELFER_DEV_SERVER_TOKEN="$(openssl rand -hex 16)"
   ```

2. Enable dev server:

   ```bash
   export SETUPHELFER_DEV_SERVER_ENABLED=true
   export SETUPHELFER_DEV_SERVER_MODE=local_lab
   export SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN=true
   ```

3. Optional read-only SSH:

   ```bash
   export SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=true
   ```

4. Restart backend (only after runtime gate approval and deploy).

5. Check health:

   ```bash
   curl -s http://127.0.0.1:8000/api/dev-server/health | jq .
   ```

6. Test ingest:

   ```bash
   curl -s -X POST http://127.0.0.1:8000/api/dev-server/ingest/report \
     -H "Content-Type: application/json" \
     -H "X-Dev-Server-Token: $SETUPHELFER_DEV_SERVER_TOKEN" \
     -d '{"node":{"node_id":"lab-vm-1","node_kind":"vm"},"report":{"lab_mode":"local_lab","report_type":"manual","payload":{}}}'
   ```

7. Open Development Cockpit — “Development Server” panel.

## Out of scope for this MVP

- Remote backup / restore / partition / repair
- Public cloud upload
- Agent on public rescue stick
