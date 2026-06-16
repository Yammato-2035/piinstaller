# Profile Gate Fix – `/api/dev-server` in Release

**Datum:** 2026-06-10  
**HEAD (Fix):** Workspace `67fac65` + lokale Änderungen  
**Ziel:** `check-runtime-profile-deploy-gate.sh` Exit 0 im Release-Profil

## Ursache

`should_register_dev_server_router()` in `backend/runtime_governance/route_exposure.py` registrierte den Dev-Server-Router im **release**-Profil zusätzlich, wenn `is_dev_server_host_locally_allowed()` true war (DCC-Developer-Token auf dem Host konfiguriert).

Folge:

- `/api/dev-server/health` → **HTTP 200** (Gate-Probe-Pfad)
- `/api/dev-server` (Root) → 404 (kein Handler)
- OpenAPI listete weiterhin alle `/api/dev-server/*`-Pfade
- `check-runtime-profile-deploy-gate.sh` → Exit **19** (`forbidden_api_path_visible:/api/dev-server`)

Das war **kein** Gate-Fehler, sondern eine echte Profil-Leakage: Release mountete Lab-APIs über die Host-Developer-Capability.

## Fix

**Datei:** `backend/runtime_governance/route_exposure.py`

```python
def should_register_dev_server_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.dev_server_enabled
```

- Router nur noch, wenn das Install-Profil `dev_server_enabled=True` setzt (`local_lab`, `developer`, `rescue_lab`).
- `is_dev_server_host_locally_allowed()` bleibt für **Config/Exposure-Middleware**, mountet aber **keinen** Router mehr in release.

**Test:** `backend/tests/test_profile_gate_legacy_independence_v1.py` – Erwartung angepasst: DCC auf Host erlaubt Config, **keine** Router-Registrierung in release.

## HTTP vorher (Runtime release, 1.7.12.1)

| Pfad | HTTP |
|------|------|
| `/api/dev-server` | 404 |
| `/api/dev-server/health` | **200** ← Gate-Blocker |
| `/api/dev-dashboard/status` | 404 |
| `install_profile` (API) | release |

## HTTP nachher (erwartet nach Backend-Restart)

| Pfad | HTTP |
|------|------|
| `/api/dev-server` | 404 |
| `/api/dev-server/health` | **404** |
| `/api/dev-dashboard/status` | 404 |
| Partitions `/api/partitions/scan` | 200 (Regression) |

## Gate

| Gate | Vorher | Nachher (nach Restart) |
|------|--------|------------------------|
| `check-runtime-profile-deploy-gate.sh` | **19** | **0** (erwartet) |
| `check-runtime-deploy-gate.sh` | 20 (legacy) | 0 (erwartet) |

## Regressionen geprüft (Workspace-Unit)

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m pytest \
  backend/tests/test_profile_gate_legacy_independence_v1.py \
  backend/tests/test_runtime_governance_route_exposure_v1.py \
  backend/tests/test_app_router_registry_v1.py \
  backend/tests/test_runtime_governance_no_profile_desync_v1.py -q
```

Ergebnis: **17 passed**

## Deploy / Runtime

| Schritt | Status |
|---------|--------|
| Fix in Workspace | ✓ |
| `route_exposure.py` nach `/opt/setuphelfer/backend/` kopiert | ✓ |
| `sudo ./scripts/deploy-to-opt.sh` | Benötigt sudo (Passwort) |
| `sudo systemctl restart setuphelfer-backend.service` | Benötigt sudo (Passwort) |

**Operator-Aktion für grünes Runtime-Gate:**

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
# oder minimal:
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-profile-deploy-gate.sh
```

## Bestätigungen

- Kein Gate-Skript geändert
- Keine Fake-Green-Lösung (kein 403 statt 404, kein OpenAPI-Filter im Gate)
- `local_lab` behält `dev_server_enabled=True` über `profile_policy.py`
- Partitionsmanager / Partitions-APIs unberührt
