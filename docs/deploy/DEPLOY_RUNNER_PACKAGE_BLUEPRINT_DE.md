# Deploy Runner Package Blueprint (read-only)

## Ziel

Blueprint fuer eine spaetere manuelle Runner-Installation, ohne Build oder Installation in dieser Phase.

## Inhalte

- Paketmodell (debian/manual/unknown) ohne Auto-Installation
- File-/Directory-/Permission-Manifest
- Sudoers-Manifest mit `install_automatically=false`
- Rollback-Manifest und Validation-Plan mit `auto_allowed=false`

## API

- `POST /api/deploy/runner/package/blueprint`
