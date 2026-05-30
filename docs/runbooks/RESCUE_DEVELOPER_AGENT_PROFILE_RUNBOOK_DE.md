# Runbook: Rescue Developer Agent Profile (DE)

## Validierung (kein Build)

```bash
cd /home/volker/piinstaller
./scripts/check-dev-agent-rescue-profile-guard.sh

PYTHONPATH=/home/volker/piinstaller/backend:/home/volker/piinstaller \
python3 -m backend.devserver_agent.cli \
  --validate-rescue-profile \
  --profile-root build/rescue/profiles/developer \
  --json
```

## Voraussetzungen für Live-Nutzung

- Development Server runtime grün (`/api/dev-server/health`)
- Developer Edition Profil im Rescue-System installiert
- **Kein** Public-Profil mit AUTO_UPLOAD=true

## Nicht in diesem Runbook

- ISO-Build, lb build, chroot, USB-Write
