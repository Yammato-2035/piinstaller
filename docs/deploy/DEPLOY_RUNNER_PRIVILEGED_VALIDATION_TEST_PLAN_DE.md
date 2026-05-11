# Deploy Runner Privileged Validation Dry-run Testdesign (read-only)

## Ziel

Konkretes Testdesign fuer die spaetere privilegierte Runner-Validierung im Dry-run ohne reale Schreiboperationen.

## Inhalte

- Preconditions, manuelle Testschritte und Negativtests
- Pflicht-Evidence inkl. UID/GID-/Audit-/Lock-Nachweisen
- Risk-Controls, Stop-Conditions und Rollback

## API

- `POST /api/deploy/runner/privileged-validation/test-plan`
