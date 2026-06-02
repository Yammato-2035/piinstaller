# Wissensbasis: app.py-Decomposition

## Was app.py künftig darf

- Bootstrap: `create_app`, Middleware- und Router-Registry-Aufrufe
- Übergangsweise: registrierte Kern-Endpoints bis Phase B

## Was app.py nicht mehr darf (Ziel)

- Dev-Dashboard-Status selbst berechnen
- Optionale Router per try/except verstreut registrieren
- Safety-/Storage-/Mount-Logik duplizieren

## Router-Registrierung

Zentral in `app_bootstrap.router_registry`. Optionale Router dürfen `import_failed` melden, ohne Uvicorn-Start zu beenden.

## Profile

- **release:** Dev-Dashboard-API blockiert (`PROFILE_ROUTE_BLOCKED`); Rescue-Agent-Router typisch disabled
- **local_lab:** Dev-Server, Fleet, Dev-Diagnostics nach bestehenden `install_profile`-Hilfsfunktionen

## Deploy-Drift

Workspace-Änderungen an Bootstrap/Rescue-Agent sind **nicht** live, bis Operator `deploy-to-opt` + Restart. Keine Live-Grün-Aussage ohne Gate.

## ISO-Build

Erst nach Deploy-Gate und Boundary-Review (`ready_for_controlled_iso_build_precheck`).
