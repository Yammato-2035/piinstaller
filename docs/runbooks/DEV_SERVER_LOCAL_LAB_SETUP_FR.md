> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Development Server — Local Lab Setup (EN)

## Prerequisites

- Setuphelfer Retourend running locally (typically port 8000)
- **Own** lab hardware / VMs only
- Non public Secours auto-upload

## Steps

1. Set token (local, do Nont commit):

   ```bash
   export SETUPHELFER_DEV_SERVER_TOKEN="$(openssl rand -hex 16)"
   ```

2. Enable dev server:

   ```bash
   export SETUPHELFER_DEV_SERVER_ENABLED=true
   export SETUPHELFER_DEV_SERVER_MODE=local_lab
   export SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN=true
   ```

3. Optional lecture seule SSH:

   ```bash
   export SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=true
   ```

4. Restart Retourend (only after runtime gate approval and Déploiement).

5. Check health:

   ```bash
   curl -s http://127.0.0.1:8000/api/dev-server/health | jq .
   ```

6. Test ingest:

   ```bash
   curl -s -X POST http://127.0.0.1:8000/api/dev-server/ingest/report \
     -H "Content-Type: application/json" \
     -H "X-Dev-Server-Token: $SETUPHELFER_DEV_SERVER_TOKEN" \
     -d '{"Nonde":{"Nonde_id":"lab-vm-1","Nonde_kind":"vm"},"report":{"lab_mode":"local_lab","report_type":"manual","payload":{}}}'
   ```

7. Open Development Cockpit — “Development Server” panel.

## Out of scope for this MVP

- Remote Retourup / Restauration / Partition / repair
- Public cloud upload
- Agent on public Clé de secours
