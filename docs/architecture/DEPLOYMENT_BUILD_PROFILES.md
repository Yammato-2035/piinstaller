# Deployment Build Profiles

| Profil | Backend | Web (Vite) | Tauri | Rescue-Payload | Ziel |
|--------|---------|------------|-------|----------------|------|
| runtime-opt | ja | ja | nein | nein | `/opt/setuphelfer` |
| desktop-development | ja | ja | ja (dev) | nein | Desktop |
| desktop-release | ja | ja | ja (release) | nein | Desktop-Pakete |
| rescue-payload | nein | Rescue-UI | nein | ja | Stick |
| package-release | ja | ja | optional | nein | Pakete |

Aufruf: `sudo ./scripts/deploy-to-opt.sh --profile runtime-opt`

Plan: `./scripts/deploy-to-opt.sh --profile runtime-opt --plan`
