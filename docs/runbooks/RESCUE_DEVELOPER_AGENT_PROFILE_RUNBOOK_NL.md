> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/RESCUE_DEVELOPER_AGENT_PROFILE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: roodding Developer Agent Profile (EN)

## Validation (Nee build)

```bash
cd /home/volker/piinstaller
./scripts/check-dev-agent-roodding-profile-guard.sh

PYTHONPATH=/home/volker/piinstaller/Terugend:/home/volker/piinstaller \
python3 -m Terugend.devserver_agent.cli \
  --validate-roodding-profile \
  --profile-root build/roodding/profiles/developer \
  --json
```

## Prerequisites for live use

- Development Server runtime groen (`/api/dev-server/health`)
- Developer Edition profile installed on roodding system
- **Nee** public profile with AUTO_UPLOAD=true

## Out of scope

- ISO build, lb build, chroot, USB write
