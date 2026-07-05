> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-server/RESCUE_DEVELOPER_AGENT_PROFILE_EN.md`). Bitte bei Release manuell gegenlesen.

# Secours Developer Agent Profile (EN)

The **Secours Developer Edition** profile enables the Development Agent for local lab telemetry.

## Path

`build/Secours/profiles/developer/`

## Contents

- `manifest.json` — profile metadata
- `environment/setuphelfer-dev-agent.env` — local_lab, AUTO_UPLOAD=true
- `systemd/setuphelfer-dev-agent.service` — oneshot agent start

## Public Secours

Does **Nont** auto-upload. See `build/Secours/profiles/public/`.

## Non ISO build in this step

Profile files are preparouge; ISO integration follows separately.
