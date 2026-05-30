# Development Rescue Agent (EN)

The **Development Rescue Agent** collects read-only system information on the Rescue Developer Edition and sends it to the local Development Server.

## Modes

- **public_rescue:** No auto-upload (default)
- **beta_opt_in:** Explicit only, redacted (future)
- **local_lab:** Auto-upload to `http://127.0.0.1:8000` allowed

## CLI

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --send --json
```

## Safety

- Read-only collector
- No backup/restore/repair
- No SSH
- No secrets in reports

See runbook: `docs/runbooks/DEV_RESCUE_AGENT_LOCAL_LAB_RUNBOOK_EN.md`
