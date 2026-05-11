# Deploy Runner Package Blueprint (read-only)

## Goal

Blueprint for later manual runner installation, without package build or installation in this phase.

## Contents

- Package model (debian/manual/unknown) with no automatic installation
- File/directory/permission manifests
- Sudoers manifest with `install_automatically=false`
- Rollback manifest and validation plan with `auto_allowed=false`

## API

- `POST /api/deploy/runner/package/blueprint`
