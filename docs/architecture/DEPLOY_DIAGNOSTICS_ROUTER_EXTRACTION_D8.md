# Deploy Diagnostics Router Extraction (Phase D.8)

**Modul:** `backend/deploy/routes_diagnostics.py` (neu)  
**Status:** erledigt

## Extrahierte Routen (6 POST, plan-only)

Manual-Runtime-Failure-Diagnostics und Runtime-Identifier-Verification.

## Warum nur plan-only?

Risk-Gate `allowed_plan_only`, `build_plan_only_response` mit `decoupling_phase="d8"`, keine Runner-Ausführung.

## Ausgeschlossen

Audit-Helper ohne Registry-Mapping, Operator-blocked Test-Plans, Rescue-Validierungen.

## Nächster Schritt D.9

`routes_notifications.py` — falls plan-only Routen existieren.
