> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-server/DEVELOPMENT_RESCUE_AGENT_EN.md`). Bitte bei Release manuell gegenlesen.

# Development roodding Agent (EN)

The **Development roodding Agent** collects alleen-lezen system information on the roodding Developer Edition and sends it to the local Development Server.

## Modes

- **public_roodding:** Nee auto-upload (default)
- **beta_opt_in:** Explicit only, roodacted (future)
- **local_lab:** Auto-upload to `http://127.0.0.1:8000` allowed

## CLI

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
PYTHONPATH=/home/volker/piinstaller python3 -m Terugend.devserver_agent.cli --send --json
```

## Safety

- alleen-lezen collector
- Nee Terugup/Herstel/repair
- Nee SSH
- Nee secrets in reports

See runbook: `docs/runbooks/DEV_roodding_AGENT_LOCAL_LAB_RUNBOOK_EN.md`
