# DCC-VIS-001 — Visible Roadmap & Changelog

## Änderungen

- `frontend/src/dcc/visibility/` — Datenmodell (Runtime-Status, Changelog, Handoff)
- `DccRuntimeStatusPanel`, `DccDeveloperTokenCard`, `DccVisibleResultsPanel`, `DccWorkspaceHandoffCard`
- `loadDevDashboard` — `localApiReachable` getrennt von `apiReachable`
- `governanceMatrix` — kein pauschales `backend_api_unreachable` bei erreichbarer Local API

## Nachweis

- `bash scripts/run-tests.sh` — grün
- `bash scripts/check-dcc-vis-001-safety.sh` — grün

## Bekannte Einschränkung

Runtime Gate bleibt rot bis Phase 0 — bewusst, kein Fake-Green.
