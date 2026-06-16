# DEVELOPMENT_SERVER_LOCAL_CAPABILITY_BACKEND_RESTART_OPERATOR_RESULT

**Datum:** 2026-06-06  
**Prompt:** `DEVELOPMENT_SERVER_LOCAL_CAPABILITY_BACKEND_RESTART_OPERATOR_RUN`  
**HEAD vorher/nachher:** `345187b` (unverändert) · **Commit/Push:** nein

## Ergebnis

**Erfolg** — Backend- und Web-UI-Prozess laufen mit frischem Stand; Dev-Server-Routen in OpenAPI registriert; Capability-, Dev-Server- und Compact-Smoke mit Token **grün**. Telemetrie unverändert **200**.

## Phase 0 — Preflight (read-only)

| Prüfung | Ergebnis |
|---------|----------|
| Branch | `main` |
| HEAD | `345187b` |
| Workspace-Version | `1.7.4.1` |
| Live `/api/version` | `1.7.4.1` |
| `install_profile` | `release` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `check-backend-version-gate.sh` | **OK** |
| `verify_deploy_to_opt --phase all` | **ok=True** |
| Ohne Token | `developer_capability_valid=false`, `dcc_visible=false` ✓ |

## Phase 1 — Prozess vor Restart (Referenz Deploy-Run)

Aus `DEVELOPMENT_SERVER_LOCAL_CAPABILITY_DEPLOY_OPERATOR_RESULT` (unmittelbar vor Restart):

| Feld | Wert |
|------|------|
| Backend-PID (alt) | ~1062771 |
| OpenAPI `/api/dev-server/*` | **0 Routen** |
| `/api/dev-server/health` | **404** `PROFILE_ROUTE_BLOCKED` |
| Compact `dev_server.enabled` | **false** |
| Klassifikation | `DEPLOY_NOT_APPLIED_OR_OLD_RUNTIME_PROCESS` |

## Phase 2 — Operator-Restart

| Aktion | Ergebnis |
|--------|----------|
| Agent `sudo systemctl restart …` | **blockiert** (kein sudo-Passwort) |
| Beobachteter Restart | **ja** — `ActiveEnterTimestamp` **2026-06-06 15:11:58 CEST** (Backend + Web-UI) |
| Backend-PID (neu) | **1063863** |
| Web-UI-PID | **1063873** |
| `setuphelfer-backend.service` | **active (running)** |
| `setuphelfer.service` | **active (running)** |
| Live `/api/version` nach Restart | **1.7.4.1** ✓ |

## Phase 3 — Gates nach Restart

| Prüfung | Ergebnis |
|---------|----------|
| `check-backend-version-gate.sh` | **OK** |
| `check-packaging-version-gate` | **OK** (Warn semver-Projektion — kein Fehler) |
| `verify_deploy_to_opt --phase all` | **ok=True** |

## Phase 4 — Token

| Feld | Ergebnis |
|------|----------|
| Token konfiguriert | ja |
| `TOKEN_LEN` | **64** (Wert nicht geloggt) |

## Phase 5 — OpenAPI Dev-Server-Routen

| Zeitpunkt | `/api/dev-server/*` Count | Weitere Routen |
|-----------|---------------------------|----------------|
| Vor Restart (Deploy-Evidence) | **0** | compact/capability/telemetry wie erwartet |
| Nach Restart (Live) | **14** | `/api/dev-dashboard/compact-status`, `/api/dev-dashboard/capability-status`, `/api/rescue/telemetry/health`, `/api/rescue/telemetry/v1/ingest` |

Beispiel Dev-Server-Pfade: `/api/dev-server/health`, `/api/dev-server/summary`, `/api/dev-server/nodes`, …

## Phase 6 — DCC Capability Smoke

### Ohne Token

| Endpunkt | HTTP | Hinweis |
|----------|------|---------|
| `/api/dev-dashboard/status` | **404** | blockiert ✓ |
| `/api/dev-dashboard/capability-status` | **200** | `DEVELOPER_CAPABILITY_REQUIRED`, `dcc_visible=false` ✓ |

### Mit Token

| Feld / Endpunkt | Ergebnis |
|-----------------|----------|
| `developer_capability_valid` | **true** |
| `dcc_visible` | **true** |
| `dev_server_locally_allowed` | **true** |
| `/api/dev-dashboard/status` | **HTTP 200** ✓ |

## Phase 7 — Dev-Server Smoke

| Endpunkt | HTTP | Body (Auszug) |
|----------|------|---------------|
| `/api/dev-server/health` | **200** | `enabled=true`, `mode=local_lab`, `storage_ok=true`, `errors=[]` |
| `/api/dev-server/summary` | **200** | — |

Kein `PROFILE_ROUTE_BLOCKED`.

## Phase 8 — Compact-Status

| Feld | Wert |
|------|------|
| `status` | `ok` |
| `dcc_visible` | **true** |
| `developer_capability.valid` | **true** |
| `dev_server.enabled` | **true** |
| `dev_server.mode` | **`local_lab`** |
| `dev_server.host_locally_allowed` | **true** |
| `dev_server.routes_available` | **true** |
| `telemetry.health_ok` | **true** |
| `telemetry.ingest_enabled` | **true** |
| `/api/rescue/telemetry/health` | **HTTP 200** |

## Phase 9 — Browser-DCC

| Prüfung | Ergebnis |
|---------|----------|
| URL | `http://127.0.0.1:3001/?window=cockpit` (nicht `:8080`) |
| HTTP-Reachability | **200** |
| API-Smoke mit Token | grün → DCC-Inhalt sollte mit gespeichertem Developer-Token laden |
| Automatisierter Browser-Snapshot | nicht ausgeführt |

Bei sichtbar blockiertem DCC trotz curl-200: Token im DCC speichern, Hard Reload.

## Erfolgskriterien

| Kriterium | Status |
|-----------|--------|
| Backend nach Restart aktiv | ✓ |
| Live Version `1.7.4.1` | ✓ |
| Version-Gate | ✓ |
| Deploy-Verify | ✓ |
| DCC mit Token HTTP 200 | ✓ |
| Dev-Server in OpenAPI | ✓ (14 Routen) |
| Dev-Server nicht `PROFILE_ROUTE_BLOCKED` | ✓ |
| Compact `dev_server.enabled=true` | ✓ |
| Telemetrie 200 | ✓ |

**Gesamt: grün**

## Fehlerklassifikation (nicht zutreffend)

- `DEVSERVER_ROUTER_NOT_REGISTERED_AFTER_RESTART` — nein  
- `DEVSERVER_COMPACT_STATUS_MISSING_FIELD` — nein  
- `DEVSERVER_CAPABILITY_CONFIG_NOT_EFFECTIVE_AFTER_RESTART` — nein  
- `DCC_BROWSER_TOKEN_NOT_STORED` — nicht festgestellt (API grün)

## Next Prompt

**`RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`**

Parallel Rescue-Track unverändert offen.

## Nicht ausgeführt

- Commit, Push  
- Deploy / manueller `cp`-Sync  
- ISO-Rebuild, USB-Write  
- Backup, Restore, Windows-Inspect  
- `apt install/upgrade`  
- Token-Werte loggen  
- Versionserhöhung  

## Secrets

Keine Token-Werte in dieser Datei.
