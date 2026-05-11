# Deploy Runner Release Readiness Matrix (read-only)

## Ziel

Zentrale Readiness-Matrix fuer die Runner-/Deploy-Write-Kette mit Status, Risiken und Gaps.

## Statusmodell

- `blocked`: blockierende Gaps vorhanden
- `review_required`: keine blocker, aber Reviews/Gaps offen
- `ready_for_lab`: lab-faehig, keine Produktionsfreigabe

## API

- `POST /api/deploy/runner/release/readiness`
