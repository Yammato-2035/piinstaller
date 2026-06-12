# KB: APP Router Slice E.1

Kurzfassung für Entwickler und Cursor-Prompts.

## Was wurde gemacht?

Vier read-only GET-Routen aus `backend/app.py` nach `backend/api/routes/health.py` und `version.py` verschoben. `app.py` bindet sie per `include_router` ein — **keine URL-Änderung**.

## Wann diesen Slice erweitern?

Nur für GET/read-only Routen ohne subprocess, ohne Backup/Restore/Deploy/Rescue, ohne neue Storage-/Safety-Logik.

## Prüfliste vor E.2

1. `MODULE_CATALOG.md` — kein Duplikat anlegen
2. `DO_NOT_DUPLICATE_RULES.md` — Facades nutzen
3. `scripts/check-module-boundaries.sh` — E.1-Warnungen beobachten

Details: [APP_ROUTER_SLICE_E1.md](../../architecture/APP_ROUTER_SLICE_E1.md)
