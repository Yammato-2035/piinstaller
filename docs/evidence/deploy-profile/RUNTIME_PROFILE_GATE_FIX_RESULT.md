# Runtime Profile Gate — Fix Ergebnis

**Datum:** 2026-05-31

## Änderungen

| Datei | Änderung |
|-------|----------|
| `scripts/check-runtime-profile-deploy-gate.sh` | Eigenständig; kein Legacy-Gate-Zwang |
| `scripts/runtime_profile_deploy_gate_eval.py` | HTTP-Sonde (2xx = sichtbar); `opt`→`release`; Capability-aware OpenAPI |
| `backend/core/install_profile.py` | `opt`-Mapping; Release ignoriert Dev-Env-Overrides; Audit nur bei Capability/HTTP |
| `scripts/check-runtime-deploy-gate.sh` | Markierung `LEGACY_GATE_NON_PROFILE_AWARE` |
| `backend/app.py` | `runtime_install_location` in `/api/version` |

## Verhalten

| Check | Release |
|-------|---------|
| `/api/dev-dashboard/status` 404 | **OK** (Profil-Gate) |
| Legacy-Gate dev-dashboard 404 | **Exit 20** (erwartet, Legacy) |
| `/api/dev-server` HTTP 200 | **Exit 19** bis Redeploy/Profil-Fix live |

## Tests

- `test_profile_gate_legacy_independence_v1.py` — 4/4
- Gesamt Profil-Suite: **23/23** OK
- Shell-Gate-Test: OK

## Live (Workspace-Gate-Skript, Runtime cea84e6)

- Profil-Gate: Exit **19** (`forbidden_api_path_visible:/api/dev-server`) — korrekte Meldung, Redeploy mit neuem `install_profile.py` nötig
- Legacy-Gate: Exit **20** (dev-dashboard 404) — informational
