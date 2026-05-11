# Deploy Runner Installationsplan (read-only)

## Ziel

Sicherer Plan fuer die spaetere privilegierte Runner-Integration ohne Ausfuehrung in dieser Phase.

## Kernpunkte

- Kein Root-Backend
- Kein Daemon-/Service-Modell
- One-shot Runner mit festem Interpreter- und Runner-Pfad
- Jobverzeichnis unter `/var/lib/setuphelfer/deploy-jobs/`
- Sudoers nur als Plantext, nicht installiert
- Manuelle Schritte verpflichtend (`auto_allowed=false`)

## Modul

`backend/deploy/runner_install_plan.py` mit `build_runner_install_plan(...)`.

## API

Read-only:
- `POST /api/deploy/runner/install/plan`

Keine apply/install/execute Route in dieser Phase.
