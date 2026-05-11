# Deploy Runner Manual Runtime Precheck (read-only)

## Ziel

Vor jedem manuellen Runtime-Runbook-Lauf eine klare Startbereitschaft pruefen, ohne Ausfuehrung zu starten.

## Umfang

- Runbook-Auswahlvalidierung (nur 7 erlaubte Runbooks)
- Environment-/Operator-/Testmedia-Checks
- Evidence-Plan unter `docs/evidence/runtime-results/`
- Stop-Conditions fuer fail-closed Abbruch

## API

- `POST /api/deploy/runner/manual-runtime/precheck`
