# Runbook: Development Server — Local Lab Setup (DE)

## Voraussetzungen

- Setuphelfer-Backend läuft lokal (typisch Port 8000)
- Nur **eigene** Lab-Hardware / VMs
- Kein Public-Rescue-Auto-Upload

## Schritte

1. Token setzen (lokal, nicht committen):

   ```bash
   export SETUPHELFER_DEV_SERVER_TOKEN="$(openssl rand -hex 16)"
   ```

2. Dev-Server aktivieren:

   ```bash
   export SETUPHELFER_DEV_SERVER_ENABLED=true
   export SETUPHELFER_DEV_SERVER_MODE=local_lab
   export SETUPHELFER_DEV_SERVER_REQUIRE_TOKEN=true
   ```

3. Optional SSH read-only:

   ```bash
   export SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=true
   ```

4. Backend neu starten (nur nach Runtime-Gate-Freigabe und Deploy).

5. Health prüfen:

   ```bash
   curl -s http://127.0.0.1:8000/api/dev-server/health | jq .
   ```

6. Test-Ingest:

   ```bash
   curl -s -X POST http://127.0.0.1:8000/api/dev-server/ingest/report \
     -H "Content-Type: application/json" \
     -H "X-Dev-Server-Token: $SETUPHELFER_DEV_SERVER_TOKEN" \
     -d '{"node":{"node_id":"lab-vm-1","node_kind":"vm"},"report":{"lab_mode":"local_lab","report_type":"manual","payload":{}}}'
   ```

7. Development Cockpit öffnen — Panel „Development Server“.

## Nicht in diesem MVP

- Backup / Restore / Partitionierung / Reparatur remote
- Public Cloud Upload
- Agent auf Public Rescue Stick
