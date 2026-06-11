# Deploy Evidence Router Extraction (Phase D.7)

**Modul:** `backend/deploy/routes_evidence.py` (erweitert)  
**Status:** erledigt

## Extrahierte Routen (6 POST, plan-only)

Zusätzlich zu D.4 (6 Routen) — D.7-Slice:

1. `/legacy-identifier-cleanup-classification`
2. `/legacy-runtime-compatibility-inventory`
3. `/legacy-runtime-coexistence-analysis`
4. `/runner/manual-runtime/failure-test-results`
5. `/runner/manual-runtime/failure-result-evaluation`
6. `/runner/manual-runtime/result-validator-seal-consistency-audit`

## Warum nur plan-only?

Risk-Gate `allowed_plan_only`, keine Runner-Ausführung, `build_plan_only_response` mit `decoupling_phase="d7"`.

## Warum POST beibehalten?

API-Kompatibilität — Clients und OpenAPI bleiben unverändert.

## Ausgeschlossen

Rescue-Evidence, Execute/Write/Apply, Operator-blocked Routen.

## Nächster Schritt D.8

`routes_diagnostics.py` — diagnostics Router (read-only/plan-only).
