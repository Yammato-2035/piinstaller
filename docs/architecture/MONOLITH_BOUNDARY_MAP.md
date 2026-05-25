# Monolith Boundary Map

## Ziel

Diese Datei dokumentiert bewusst die noch vorhandenen Monolith-Grenzen. Ihr Vorhandensein ist Evidence fuer Transparenz, nicht fuer abgeschlossene Entkopplung.

## Weiterhin gekoppelte Bereiche

- `backend/app.py`: zentrale Route-Registrierung und viele fachliche Einstiege
- Deploy-/Runtime-Governance: Runtime-Gate, Deploy-Helper, Update-Status
- Rescue-ISO-Readiness: State, Executor, Operator-Commands und Evidence

## Bereits klar abgegrenzte read-only Bereiche

- `backend/core/update_check.py`
- `backend/core/packaging_readiness_state.py`
- `backend/core/project_overview_dashboard_state.py`

## Konsequenz

Solange `backend/app.py` und die Deploy-/Rescue-Strecken noch als zentrale Integrationspunkte dienen, bleibt der Monolith-Status absichtlich `yellow`.
