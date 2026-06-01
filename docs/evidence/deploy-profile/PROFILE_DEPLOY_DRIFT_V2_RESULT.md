# Profile Deploy Drift V2 — Ergebnis

**Datum:** 2026-05-31

## Umsetzung

| Komponente | Status |
|------------|--------|
| `enrich_deploy_drift_profile_aware()` in `profile_deploy_manifest.py` | implementiert |
| Integration in `_compute_deploy_drift()` | implementiert |
| `runtime_deploy_gate_eval.py` | `profile_manifest_match` berücksichtigt Exit 16 |
| `audit_frontend_backend_profile()` | Backend/Frontend-Abgleich |
| `/api/version` | `frontend_build_id`, Mismatch-Felder |

## deploy_drift-Struktur (profilbewusst)

- `profile_aware: true`
- `install_profile`, `manifest_profile`, SHA256-Felder
- `forbidden_paths_present`, `required_paths_missing`
- `forbidden_api_paths_visible`, `required_api_paths_missing`
- `public_exposure_status`
- `profile_manifest_match` steuert Legacy-`manifest_match` bei Übereinstimmung

## Tests

- `test_profile_deploy_drift_v2.py` — 4/4 OK
- Gesamt Profil-Suite: 19/19 OK

## Live

- **pending:** Deploy nach `/opt` erfordert `sudo ./scripts/deploy-to-opt.sh` (sudo_nopass=no in diesem Lauf).
