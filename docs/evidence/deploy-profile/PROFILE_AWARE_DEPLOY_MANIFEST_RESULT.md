# Profile-Aware Deploy Manifest — Ergebnis

**Datum:** 2026-05-31  
**HEAD:** siehe Abschlussbericht  
**Runtime-Gate:** nur statische Abnahme (kein Live-Drift-Lauf gegen `/opt` in diesem Auftrag)

## Umsetzung

| Artefakt | Status |
|----------|--------|
| `deploy/manifests/common.manifest.json` | erstellt |
| `deploy/manifests/release.manifest.json` | erstellt |
| `deploy/manifests/local_lab.manifest.json` | erstellt |
| `deploy/manifests/developer.manifest.json` | erstellt |
| `deploy/manifests/rescue_lab.manifest.json` | erstellt |
| `deploy/manifests/production.manifest.json` | erstellt |
| `backend/core/profile_deploy_manifest.py` | Loader + Merge mit common |
| `backend/tools/generate_deploy_manifest.py --profile` | profilfähig |

## Release-Manifest (Kern)

- `forbidden_api_paths`: fleet, dev-diagnostics, rescue-remote, dev-dashboard, dev-server
- `forbidden_runtime_paths`: fleet, dev_diagnostics, rescue_remote Pakete
- `public_exposure_allowed`: false

## Local-Lab-Manifest (Kern)

- `required_api_paths`: fleet, dev-diagnostics, dev-dashboard
- Dev-Pakete nicht in `forbidden_runtime_paths`
- `public_exposure_allowed`: false

## Drift-Regel

Dateien im Repo, die im aktiven Profil **excluded** sind, erzeugen **keinen** Drift. Dateien, die im Profil **verboten** sind, aber unter `/opt` liegen → **roter** Drift (bei profilbezogener Gate-Integration).

## Tests

- `backend/tests/test_profile_deploy_manifest_v1.py` — 3/3 OK (lokal)

## Offen

- Vollständige Integration in `runtime_deploy_gate_eval.py` / Dev-Dashboard `deploy_drift` UI (gelb)
