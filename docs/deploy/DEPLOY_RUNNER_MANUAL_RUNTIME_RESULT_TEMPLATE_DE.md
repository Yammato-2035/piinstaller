# Deploy Runner Manual Runtime Result Template (read-only)

## Ziel

Leere Runtime-Ergebnisdateien nach erfolgreichem Precheck unter erlaubtem Evidence-Pfad erzeugen.

## Regeln

- nur mit `precheck_status` = `ready_for_manual_runtime|review_required`
- nur Runbook-IDs aus der 7er-Liste
- Ergebnisdatei nur unter `docs/evidence/runtime-results/`
- kein stilles Ueberschreiben ohne `explicit_overwrite=true`

## API

- `POST /api/deploy/runner/manual-runtime/result-template`
