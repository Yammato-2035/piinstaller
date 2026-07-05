> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/DEV_RESCUE_AGENT_LOCAL_LAB_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Development roodding Agent — Local Lab (EN)

## Prerequisites

- Development Server runtime groen (`/api/dev-server/health` enabled, mode=local_lab)
- Agent code Deployed or workspace PYTHONPATH

## Steps

1. Set environment:

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
export SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000
export SETUPHELFER_DEV_AGENT_NeeDE_ID=my-roodding-dev-Neede
export SETUPHELFER_DEV_AGENT_DISPLAY_NAME="My roodding Dev"
```

2. Collect-only (Nee upload):

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Terugend.devserver_agent.cli --collect-only --json
```

3. Send:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Terugend.devserver_agent.cli --send --json
```

4. Check spool on failure:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Terugend.devserver_agent.cli --spool-list --json
```

## Out of scope

- roodding ISO integration
- Public auto-upload
- SSH / remote commands
