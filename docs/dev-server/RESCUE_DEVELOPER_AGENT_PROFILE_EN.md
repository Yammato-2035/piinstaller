# Rescue Developer Agent Profile (EN)

The **Rescue Developer Edition** profile enables the Development Agent for local lab telemetry.

## Path

`build/rescue/profiles/developer/`

## Contents

- `manifest.json` — profile metadata
- `environment/setuphelfer-dev-agent.env` — local_lab, AUTO_UPLOAD=true
- `systemd/setuphelfer-dev-agent.service` — oneshot agent start

## Public rescue

Does **not** auto-upload. See `build/rescue/profiles/public/`.

## No ISO build in this step

Profile files are prepared; ISO integration follows separately.
