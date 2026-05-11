# Deploy Runner Runtime Result Validator (read-only)

## Ziel

Manuell erzeugte Runtime-Ergebnisdateien kontrolliert einlesen und gegen Schema, Reihenfolge und Evidence-Pflichtfelder validieren.

## Scope

- Nur Lesen unter `docs/evidence/runtime-results/`
- Nur `.json` Dateien
- Keine Symlinks, keine Traversal-Pfade, keine absoluten Fremdpfade
- Fail-closed bei JSON-Parsefehlern und fehlenden Pflichtfeldern

## Validierungen

- Schema-Pflichtfelder aus `RUNNER_RUNTIME_RESULT_SCHEMA.json`
- Runbook-Reihenfolge (1..7) inkl. Blockierung bei Fehler/Out-of-order
- Evidence-Pflichtfelder inkl. Write-bezogener Verify-Werte
- Safety Findings mit blockierenden Codes
- Acceptance-Entscheidung ohne automatische Freigabe

## API

- `POST /api/deploy/runner/runtime-results/validate`
