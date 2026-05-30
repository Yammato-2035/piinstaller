# Runbook: Development Rescue Agent — Local Lab (EN)

## Prerequisites

- Development Server runtime green (`/api/dev-server/health` enabled, mode=local_lab)
- Agent code deployed or workspace PYTHONPATH

## Steps

1. Set environment:

```bash
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
export SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000
export SETUPHELFER_DEV_AGENT_NODE_ID=my-rescue-dev-node
export SETUPHELFER_DEV_AGENT_DISPLAY_NAME="My Rescue Dev"
```

2. Collect-only (no upload):

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --collect-only --json
```

3. Send:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --send --json
```

4. Check spool on failure:

```bash
PYTHONPATH=/home/volker/piinstaller python3 -m backend.devserver_agent.cli --spool-list --json
```

## Out of scope

- Rescue ISO integration
- Public auto-upload
- SSH / remote commands
