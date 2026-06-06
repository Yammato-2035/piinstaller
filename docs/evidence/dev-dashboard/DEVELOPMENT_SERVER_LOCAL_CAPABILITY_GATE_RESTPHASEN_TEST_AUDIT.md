# DEVELOPMENT_SERVER_LOCAL_CAPABILITY_GATE_RESTPHASEN_TEST_AUDIT

**Datum:** 2026-06-06  
**Prompt:** `DEVELOPMENT_SERVER_LOCAL_CAPABILITY_GATE_RESTPHASEN_TEST_AUDIT`  
**HEAD:** `13b91ff` (uncommitted Fix, Branch `main`)  
**Klassifikation:** `deploy_required` / `workspace_validated_live_pending_deploy`

## 1. Git / Workspace

| Feld | Wert |
|------|------|
| HEAD | `13b91ff` |
| Branch | `main` |
| Working tree | **dirty** (Fix + viele unrelated Änderungen) |
| Fix committed | **nein** |
| Fix-relevante Dateien (Diff) | 12 Dateien, +146 / −10 Zeilen (Capability, Route-Exposure, Devserver-Config, Compact-Status, Version, Frontend-Kachel, Tests) |

## 2. Versionierung

| Quelle | Wert | OK |
|--------|------|-----|
| `config/version.json` | `1.7.4.1` | ja |
| `frontend/package.json` | `1.7.4.1` | ja |
| `frontend/package-lock.json` | `1.7.4.1` | ja |
| Cargo/Tauri Semver | `1.7.4` | ja (Projektion W=1 → Patch-Komponente) |
| `check_version_consistency.py` | ok=True | ja |
| Live `/api/version` | **`1.7.4.0`** | Drift erwartet (kein Deploy) |

**VERSION_POLICY_DRIFT:** nein

## 3. Code-Audit (Workspace)

| Prüffrage | Ergebnis |
|-----------|----------|
| Developer-Capability nur lokal | **ja** — `DCC_DEVELOPER_ENABLED` + Token-Datei/Env; optional Hostname-Binding |
| `SETUPHELFER_DEV_SERVER_ENABLED` ohne Capability ignoriert | **ja** — `test_release_ignores_dev_server_env_override_without_developer_capability` |
| Dev-Server nur mit Host-Capability auf Release | **ja** — `is_dev_server_host_locally_allowed()` + Policy/Config/Router |
| Telemetrie unabhängig | **ja** — `/api/rescue/telemetry/health` HTTP 200 ohne Token |
| DCC vs Dev-Server getrennt | **ja** — DCC: Request-Token-Gate; Dev-Server: Host-Capability + Exposure |
| Fleet/Rescue-Agent auf Release | blockiert (OpenAPI ohne `/api/fleet`, `/api/rescue-agent`) |
| `compact-status` → `dev_server` | **ja** (Workspace-Simulation) |
| Keine Secrets in API | **ja** (Unit-Tests + manuelle jq-Prüfung) |
| `profile_exposure` bei Capability | **ja** — `/api/dev-server` in Exempt-Prefixes |
| Forbidden Runtime-Pfade | weiterhin Governance-Warnung möglich; Capability blockiert DCC nicht fälschlich |

**Hinweis Architektur:** Dev-Server-Routen auf konfiguriertem Host sind über **Host-Gate** (nicht DCC-Request-Token) erreichbar — Rescue-Ingest nutzt separat `X-Dev-Server-Token`; Bind-Hint bleibt `127.0.0.1`.

### Workspace-Zielmodell (Simulation mit Token)

```json
{
  "dev_server": {
    "enabled": true,
    "mode": "local_lab",
    "host_locally_allowed": true,
    "routes_available": true,
    "require_token": true
  },
  "developer_capability": {
    "valid": true,
    "reason": "DEVELOPER_CAPABILITY_VALID",
    "dev_server_locally_allowed": true
  }
}
```

## 4. Tests

| Suite | Ergebnis |
|-------|----------|
| `check_version_consistency.py` | pass |
| `py_compile` (6 Module) | pass |
| Backend unittest (Capability, Compact, Deploy-Drift, Profile-Gate, Devserver-Profile, Deploy-Verify) | **40 OK**, 3 skipped (TestClient) |
| `test_runtime_governance_route_exposure_v1` | 7/7 OK |
| `test_development_server_capability_gate_v1.py` | **TEST_COVERAGE_GAP** (Modul fehlt) |
| Frontend `dcc` | 19 OK |
| Frontend `devserver` | 4 OK |
| Frontend `compact` | 3 OK |
| `npm run build` | OK (`1.7.4.1`) |

## 5. Live-Runtime (`/opt/setuphelfer`, **1.7.4.0**)

### Ohne Token

| Endpoint | HTTP | Kurz |
|----------|------|------|
| `/api/dev-dashboard/status` | 404 | `DEVELOPER_CAPABILITY_REQUIRED` |
| `/api/dev-dashboard/compact-status` | 200 | **ohne** Feld `dev_server` |
| `/api/dev-server/health` | 404 | Router nicht registriert |
| `/api/rescue/telemetry/health` | 200 | unabhängig OK |

### Mit Token (Länge 64, Wert nicht geloggt)

| Endpoint | Ergebnis |
|----------|----------|
| `/api/dev-dashboard/capability-status` | `dcc_visible=true`, `reason=DEVELOPER_CAPABILITY_VALID` |
| `/api/dev-dashboard/compact-status` | `ok`, **kein** `dev_server`-Objekt |
| `/api/dev-server/health` | 404 `PROFILE_ROUTE_BLOCKED` |

### OpenAPI live

- `/api/dev-dashboard/*`: **registriert**
- `/api/dev-server/*`: **nicht registriert** (0 Routen)
- `/api/rescue/telemetry/*`: **registriert**

### `verify_deploy_to_opt.py`

**ok=False** — SHA256-Mismatch u.a. `developer_capability.py`, `route_exposure.py`, `devserver/config.py`, `dev_dashboard_compact_status.py`, `version.json`; API erwartet `1.7.4.1`, live `1.7.4.0`.

## 6. Fehlerklassifikation (Live)

| Code | Root Cause | Beleg |
|------|------------|-------|
| **DEVSERVER-CAPABILITY-001** | Live-Code ohne Fix; Compact zeigt kein enabled Dev-Server | compact ohne `dev_server`, DCC sichtbar mit Token |
| **DEVSERVER-CAPABILITY-003** | Dev-Server-Router auf Live nicht geladen | OpenAPI: `dev-server routes: []` |
| **DEVSERVER-CAPABILITY-006** | `/opt` nicht synchron | verify_deploy + version 1.7.4.0 |

## 7. Operator-Handoff (nicht ausgeführt — kein Agent-sudo)

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
./scripts/check-backend-version-gate.sh
python3 backend/tools/verify_deploy_to_opt.py \
  --workspace /home/volker/piinstaller \
  --runtime /opt/setuphelfer \
  --phase all
sudo systemctl restart setuphelfer-backend
sleep 2
./scripts/check-backend-version-gate.sh
# Token aus Datei, nicht loggen:
curl -sS -H "X-Setuphelfer-Developer-Token: $(sudo cat /etc/setuphelfer/dcc_developer.token)" \
  http://127.0.0.1:8000/api/dev-dashboard/compact-status | jq '{status,dcc_visible,dev_server,telemetry}'
curl -sS -H "X-Setuphelfer-Developer-Token: $(sudo cat /etc/setuphelfer/dcc_developer.token)" \
  http://127.0.0.1:8000/api/dev-server/health | jq '{enabled,mode,storage_ok}'
```

Erwartung nach Deploy: `project_version=1.7.4.1`, OpenAPI mit `/api/dev-server/health`, Compact `dev_server.enabled=true`, Dev-Server-Health `enabled=true`, `mode=local_lab`.

## 8. Entscheidung

| Feld | Wert |
|------|------|
| Workspace-Fix | **fachlich korrekt**, Tests grün |
| Live | **noch alt** — Deploy + Backend-Neustart erforderlich |
| Status | `deploy_required` |
| **Next Prompt** | **`DEVELOPMENT_SERVER_LOCAL_CAPABILITY_DEPLOY_OPERATOR_RUN`** |
| Parallel (Rescue-Track unverändert) | **`RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`** |

## 9. Nicht ausgeführt

- Deploy nach `/opt`
- `systemctl restart`
- Commit / Push
- USB-dd, ISO-Rebuild, apt, Backup/Restore
- Profilwechsel auf `local_lab`

## Secrets

Keine Token-Werte in dieser Datei.
