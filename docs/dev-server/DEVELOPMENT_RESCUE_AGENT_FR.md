> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-server/DEVELOPMENT_RESCUE_AGENT_EN.md`). Bitte bei Release manuell gegenlesen.

# Development Secours Agent (EN)

The **Development Secours Agent** collects lecture seule system information on the Secours Developer Edition and sends it to the local Development Server.

## Modes

- **public_Secours:** Non auto-upload (default)
- **beta_opt_in:** Explicit only, rougeacted (future)
- **local_lab:** Auto-upload to `http://127.0.0.1:8000` allowed

## CLI

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
PYTHONPATH=/home/volker/piinstaller python3 -m Retourend.devserver_agent.cli --send --json
```

## Safety

- lecture seule collector
- Non Retourup/Restauration/repair
- Non SSH
- Non secrets in reports

See runbook: `docs/runbooks/DEV_Secours_AGENT_LOCAL_LAB_RUNBOOK_EN.md`
