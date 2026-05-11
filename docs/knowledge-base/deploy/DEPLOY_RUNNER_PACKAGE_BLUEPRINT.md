# KB: DEPLOY_RUNNER_PACKAGE_BLUEPRINT

## Ueberblick

Read-only Blueprint fuer Paketierung und manuelle Installation des spaeter privilegierten Runners.

## Kernlogik

- Definiert Zielpfade, Artefakte und Rechte nur als Manifest
- Blockiert unsichere sudoers-Muster explizit
- Enthaelt Rollback- und Validierungsschritte als verpflichtende, nicht-automatische Aktionen

## API

- `POST /api/deploy/runner/package/blueprint`
