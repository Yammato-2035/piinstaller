> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-server/RESCUE_DEVELOPER_AGENT_PROFILE_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding Developer Agent Profile (EN)

The **roodding Developer Edition** profile enables the Development Agent for local lab telemetry.

## Path

`build/roodding/profiles/developer/`

## Contents

- `manifest.json` — profile metadata
- `environment/setuphelfer-dev-agent.env` — local_lab, AUTO_UPLOAD=true
- `systemd/setuphelfer-dev-agent.service` — oneshot agent start

## Public roodding

Does **Neet** auto-upload. See `build/roodding/profiles/public/`.

## Nee ISO build in this step

Profile files are preparood; ISO integration follows separately.
