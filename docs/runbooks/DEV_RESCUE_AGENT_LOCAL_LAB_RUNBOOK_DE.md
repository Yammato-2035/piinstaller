# Runbook: Development Rescue Agent — Local Lab (DE)

## Voraussetzungen

- Development Server runtime grün (`/api/dev-server/health` enabled, mode=local_lab)
- Agent-Code deployed oder Workspace-PYTHONPATH

## Schritte

1. Umgebung setzen:

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
export SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000
export SETUPHELFER_DEV_AGENT_NODE_ID=my-rescue-dev-node
export SETUPHELFER_DEV_AGENT_DISPLAY_NAME="My Rescue Dev"
```

2. Collect-only (kein Upload):

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --collect-only --json
```

3. Senden:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --send --json
```

4. Spool prüfen bei Fehler:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --spool-list --json
```

## Nicht in diesem MVP

- Rescue ISO Integration
- Public Auto-Upload
- SSH / Remote Commands
