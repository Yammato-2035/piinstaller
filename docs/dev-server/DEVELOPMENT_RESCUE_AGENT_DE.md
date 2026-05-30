# Development Rescue Agent (DE)

Der **Development Rescue Agent** erfasst read-only Systeminformationen auf dem Rettungsstick Developer Edition und sendet sie an den lokalen Development Server.

## Modi

- **public_rescue:** Kein Auto-Upload (Default)
- **beta_opt_in:** Nur explizit, redigiert (später)
- **local_lab:** Auto-Upload an `http://127.0.0.1:8000` erlaubt

## CLI

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --send --json
```

## Sicherheit

- Read-only Collector
- Kein Backup/Restore/Reparatur
- Kein SSH
- Keine Secrets in Reports

Siehe Runbook: `docs/runbooks/DEV_RESCUE_AGENT_LOCAL_LAB_RUNBOOK_DE.md`
