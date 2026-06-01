# Runtime Profile Deploy Gate — Ergebnis

**Datum:** 2026-05-31

## Skripte

| Skript | Rolle |
|--------|-------|
| `scripts/check-runtime-deploy-gate.sh` | Basis (Version, Service, deploy_drift) |
| `scripts/check-runtime-profile-deploy-gate.sh` | Basis + `/api/version` + OpenAPI-Profilprüfung |
| `scripts/runtime_profile_deploy_gate_eval.py` | Evaluator (Exit 17–22, 30) |

## Exit-Codes (Profil)

| Code | Bedeutung |
|------|-----------|
| 0 | OK |
| 17 | install_profile_missing |
| 18 | profile_manifest_mismatch |
| 19 | forbidden_api_path_visible |
| 20 | required_api_path_missing |
| 21 | public_exposure_blocked |
| 22 | frontend_profile_mismatch |

## Shell-Test

`scripts/tests/test_runtime_profile_deploy_gate_v1.sh` — Release+Fleet → 19; Local-Lab mit Pfaden → 0

## Runtime-Abnahme

In diesem Auftrag: **keine** Runtime-Abnahme gegen laufendes `/opt` (nur Unit-/Shell-Tests). Wenn Basis-Gate rot: nur statische Implementierung dokumentiert.
