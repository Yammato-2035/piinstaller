# Developer Backend Watchdog — Deploy Result

**Datum:** 2026-06-03  
**HEAD:** `8fba260`

## Deploy (Agent-Session)

| Feld | Wert |
|------|------|
| Deploy ausgeführt | **no** (Operator sudo erforderlich) |
| Deploy Exit | **1** (`sudo: Ein Passwort ist notwendig`) |
| Befehl | `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller` |

**STOP** gemäß Auftrag: kein local_lab-Smoke, kein Timer, kein QEMU.

## Operator-Handoff (Terminal mit sudo)

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
echo "deploy_exit=$?"
```

Erwartung nach erfolgreichem Deploy:

- `daemon-reload` + Restart + Retry `/api/version` (15×2s) im Skript
- `/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh` vorhanden
- `/opt/setuphelfer/backend/core/dev_dashboard_backend_health.py` vorhanden
- Frontend dist mit `backend-health` im JS-Bundle

## Ist nach Agent-Lauf (unverändert)

| Prüfpunkt | Wert |
|-----------|------|
| Backend active | **yes** |
| Port 8000 listening | **yes** |
| `/api/version` HTTP 200 | **yes** |
| `/opt` Watchdog-Skript | **no** |
| `/opt` Backend-Health API/Loader | **no** |
| Frontend dist aktualisiert (Watchdog) | **no** |
| **Status** | **blocked** |
