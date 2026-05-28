# STANDALONE_CONTROL_CENTER_VISIBILITY_AUDIT

## Scope

- Static frontend/snapshot analysis.
- Build/tests for visibility-path validation.
- No runtime restart/deploy/repair action.

## Checks

1. `frontend/public/dev-dashboard.snapshot.json` exists: **yes**.
2. JSON validity (`python3 -m json.tool`): **valid**.
3. Snapshot content includes `status/modules/roadmap/areas`: **yes** (`modules` and roadmap-derived data available).
4. Snapshot contains prompt/runtime/docs/evidence-oriented data: **yes** (version/git/evidence/modules present).
5. Standalone loading path exists:
   - `loadDevDashboard()` falls back `runtime_api -> tauri_scan -> snapshot -> unavailable`.
6. Fallback banner if API offline exists: **yes** (`StandaloneModeBanner`, i18n keys present).
7. Areas hidden when API unreachable: **not by hard hide**; panels depend on `dashboard` presence.
8. i18n keys present (`de.json`, `en.json`): **yes** (`devDashboard.standalone.*`, `manualCommandRuns.*`, governance keys).
9. Routing/tab regression in inspected files: **not found**.
10. Why "almost empty" can occur in standalone:
    - If runtime API hangs and snapshot cannot be loaded in active runtime context, loader returns `unavailable` minimal dashboard.
    - Additional symptom: local frontend endpoint on `127.0.0.1:3001` was not reachable during audit while service state changed, which can result in missing standalone snapshot delivery path.

## Build/tests

- `npm --prefix frontend run build`: **pass**
- `npm --prefix frontend run test -- --run`: **pass** (10 files / 44 tests)

## Classification

- `backend_dependency_too_strong`

## Fix decision (Phase 4)

- No code fix applied in this run.
- Reason: primary blocker is runtime/backend hang plus unstable active frontend serving path, not a clearly isolated frontend-only regression in the inspected source.
- Safe next step is operator-level runtime stabilization and then targeted standalone snapshot delivery verification on the active runtime endpoint.
