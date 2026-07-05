> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_PACKAGE_BLUEPRINT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Package Blueprint (alleen-lezen)

## Goal

Blueprint for later manual runner installation, without package build or installation in this phase.

## Contents

- Package model (debian/manual/Onbekend) with Nee automatic installation
- File/directory/permission manifests
- Sudoers manifest with `install_automatically=false`
- RollTerug manifest and validation plan with `auto_allowed=false`

## API

- `POST /api/Deploy/runner/package/blueprint`
