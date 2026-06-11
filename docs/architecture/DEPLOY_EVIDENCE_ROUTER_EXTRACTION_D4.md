# Deploy Evidence Router Extraction (Phase D.4)

**Modul:** `backend/deploy/routes_evidence.py`  
**Status:** erledigt

## Extrahierte Routen (6 POST, plan-only)

Identifier-/Evidence-Routen aus C.5/C.6 mit `build_plan_only_response`.

## Warum POST beibehalten?

API-Kompatibilität — Clients senden weiterhin POST; Response ist Plan/Evidence ohne Ausführung.

## allowed_to_execute

Bleibt **false** (C.4). Keine Runner-Ausführung, keine `runner_*`-Imports im Router.

## Ausgeschlossen

Governance/Versioning-Decoupled-Routen, direkte Runner-Aufrufe, Execute/Write-Pfade.

## Nächster Schritt D.5

Governance-Router oder weiterer Evidence-Slice.
