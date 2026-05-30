# Runbook: Rescue Developer Agent Profile (EN)

## Validation (no build)

```bash
cd /home/volker/piinstaller
./scripts/check-dev-agent-rescue-profile-guard.sh

PYTHONPATH=/home/volker/piinstaller/backend:/home/volker/piinstaller \
python3 -m backend.devserver_agent.cli \
  --validate-rescue-profile \
  --profile-root build/rescue/profiles/developer \
  --json
```

## Prerequisites for live use

- Development Server runtime green (`/api/dev-server/health`)
- Developer Edition profile installed on rescue system
- **No** public profile with AUTO_UPLOAD=true

## Out of scope

- ISO build, lb build, chroot, USB write
