> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_PACKAGE_BLUEPRINT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Package Blueprint (lecture seule)

## Goal

Blueprint for later manual runner installation, without package build or installation in this phase.

## Contents

- Package model (debian/manual/Inconnu) with Non automatic installation
- File/directory/permission manifests
- Sudoers manifest with `install_automatically=false`
- RollRetour manifest and validation plan with `auto_allowed=false`

## API

- `POST /api/Déploiement/runner/package/blueprint`
