# Operator-Handoff — Deploy-Sync nach Watchdog

**Grund:** Agent-Shell kann `sudo` nicht interaktiv (Passwort/TTY).

## Befehle

```bash
cd /home/volker/piinstaller
git rev-parse --short HEAD   # erwartet 2bf64b7
sudo systemctl start setuphelfer-deploy-helper.service
journalctl -u setuphelfer-deploy-helper.service -n 120 --no-pager
./scripts/check-runtime-deploy-gate.sh
```

## Erfolg

- Gate Exit **0**
- `/opt/setuphelfer/backend/core/liveness.py` vorhanden
- Nächster Prompt: `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`

## Bei weiterem Exit 14

- `DEPLOY_DRIFT_TRIAGE_AFTER_WATCHDOG` — Journal des Deploy-Helpers prüfen

## Bei Exit 17/18

- `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF` — kein Rescue

**Nicht:** Healthcheck-Timer aktivieren, Rescue/Backup/Restore starten.
