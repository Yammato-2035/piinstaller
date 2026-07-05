> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/RESCUE_DEVELOPER_AGENT_PROFILE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Secours Developer Agent Profile (EN)

## Validation (Non build)

```bash
cd /home/volker/piinstaller
./scripts/check-dev-agent-Secours-profile-guard.sh

PYTHONPATH=/home/volker/piinstaller/Retourend:/home/volker/piinstaller \
python3 -m Retourend.devserver_agent.cli \
  --validate-Secours-profile \
  --profile-root build/Secours/profiles/developer \
  --json
```

## Prerequisites for live use

- Development Server runtime vert (`/api/dev-server/health`)
- Developer Edition profile installed on Secours system
- **Non** public profile with AUTO_UPLOAD=true

## Out of scope

- ISO build, lb build, chroot, USB write
