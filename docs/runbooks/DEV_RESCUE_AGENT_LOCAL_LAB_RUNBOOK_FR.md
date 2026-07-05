> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/DEV_RESCUE_AGENT_LOCAL_LAB_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Development Secours Agent — Local Lab (EN)

## Prerequisites

- Development Server runtime vert (`/api/dev-server/health` enabled, mode=local_lab)
- Agent code Déploiemented or workspace PYTHONPATH

## Steps

1. Set environment:

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
export SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000
export SETUPHELFER_DEV_AGENT_NonDE_ID=my-Secours-dev-Nonde
export SETUPHELFER_DEV_AGENT_DISPLAY_NAME="My Secours Dev"
```

2. Collect-only (Non upload):

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Retourend.devserver_agent.cli --collect-only --json
```

3. Send:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Retourend.devserver_agent.cli --send --json
```

4. Check spool on failure:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m Retourend.devserver_agent.cli --spool-list --json
```

## Out of scope

- Secours ISO integration
- Public auto-upload
- SSH / remote commands
