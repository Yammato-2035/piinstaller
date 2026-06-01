# Profile Deploy Drift V2 — Ist-Analyse

**Datum:** 2026-05-31 · **HEAD:** `34071c9` (Erweiterung in diesem Lauf)

## Aktueller deploy_drift-Zustand (vor V2)

- `backend/core/dev_dashboard.py` verglich feste `DEPLOY_MANIFEST_REL_PATHS` (Kern-Dateien) Workspace vs. `/opt/setuphelfer`.
- `manifest_drift_for_roots()` verglich `build/deploy/setuphelfer-deploy-manifest.json` (gesamte Whitelist, nicht profilbezogen).
- **Exit 14/16** im Basis-Gate: `manifest_match=false` oder Backend-Datei-Drift, obwohl Dev-Pakete im Repo existieren, aber nicht im Profil-Scope liegen.

## Warum Basis-Gate Exit 16 lief

- Live-Runtime (`/opt`) enthält noch **älteren Stand** als Workspace-Commit `34071c9+`.
- Legacy-Manifest-Hashes zwischen Workspace und Runtime unterschiedlich → `manifest_match=false` → Evaluator Exit **16**.

## Drift gegen gesamtes Repo?

- **Datei-Drift:** nur feste Kernpfade (nicht `backend/fleet/**` im Repo).
- **Manifest-Drift:** bisher **gesamt** (alle Manifest-Dateien), **nicht** profil-spezifisch.

## Profilmanifest vor V2

- `deploy/manifests/*.json` vorhanden, Generator `--profile`, aber Dashboard/Gate nutzten sie nicht für `deploy_drift.status`.

## Fehlende Dashboard-Felder (vor V2)

- `profile_aware`, `forbidden_paths_present`, `required_api_paths_missing`, `forbidden_api_paths_visible`, `public_exposure_status`, `profile_manifest_match`.

## /api/version live (Phase 0)

- Laufzeit ohne Deploy von `34071c9`: `install_profile=opt` (Legacy `install_paths`), **ohne** Capability-Felder.
- Nach Deploy + `SETUPHELFER_INSTALL_PROFILE`: erwartet `install_profile=release|local_lab`, `profile_gate_*`, `frontend_build_profile`.

## Release vs. local_lab (Ziel)

| Aspekt | release | local_lab |
|--------|---------|-----------|
| Dev-API | forbidden | required (fleet, dev-diagnostics, dev-dashboard) |
| Runtime-Verzeichnisse | `backend/fleet` etc. forbidden | erlaubt |
| Public Exposure | immer blockiert | blockiert |
| Frontend-Build | keine Dev-Control-UI | Lab-UI + Warnhinweis |
