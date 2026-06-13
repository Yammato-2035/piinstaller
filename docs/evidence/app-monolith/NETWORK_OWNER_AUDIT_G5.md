# Network Owner Audit — G.5

**HEAD:** `307c411` · **Branch:** `main`  
**Kanonischer Owner:** `backend/core/network_info_facade.py` (`FACADE_VERSION = 1`)

## Owner-API (öffentlich)

| Funktion | Zweck |
|----------|-------|
| `build_network_info` | Legacy-Shape Netzwerk-Info (live) |
| `build_demo_network_info` | Demo-Platzhalter |
| `build_api_status_payload` | `GET /api/status` Payload |
| `build_system_network_response` | `GET /api/system/network` Payload |
| `build_network_status_section` | Section-Wrapper |
| `normalize_legacy_network_info` | Normalisierung |
| `build_network_info_diagnostics` | Metadaten |

## Legacy-Adapter (intern, kanonisch)

| Adapter | Delegiert an |
|---------|--------------|
| `_legacy_get_network_info` | `app.get_network_info` |
| `_legacy_demo_network` | `app._demo_network` |
| `_legacy_detect_frontend_port` | `app._detect_frontend_port` |

## Importe in `network_info_facade.py`

| Import | Rolle |
|--------|-------|
| `core.dcc_status_facade.build_section_status` | Status-Vokabular (kein Network-Discovery) |
| `app` (lazy in `_legacy_*`) | Legacy-Implementierung |

Kein `subprocess`, kein `run_command`, kein `psutil`.

## Aufrufer der Facade

| Datei | Kontext | API |
|-------|---------|-----|
| `backend/api/routes/network.py` | HTTP Router G.4 | `build_api_status_payload`, `build_system_network_response` |
| `backend/app.py` | `get_system_info` (~Z.6554) | `build_network_info`, `build_demo_network_info` |
| `backend/app.py` | `webserver_status` (~Z.8502) | `build_network_info` |
| `backend/tests/test_network_info_facade_v1.py` | Contract | diverse |
| `backend/tests/test_network_info_route_migration_g2b.py` | G.2b | diverse |
| `backend/tests/test_network_info_core_cleanup_g3.py` | G.3 | diverse |
| `backend/tests/test_network_router_extraction_g4.py` | G.4 | AST/Import |

## Direktzugriffe außerhalb Facade (Backend)

| Datei | Symbol | Bewertung |
|-------|--------|-----------|
| `backend/app.py` | `def get_network_info` | **LEGACY_ADAPTER** (Implementierung) |
| `backend/app.py` | `def _demo_network` | **LEGACY_ADAPTER** |
| `backend/app.py` | `def _detect_frontend_port` | **LEGACY_ADAPTER** |
| `backend/app.py` | `webserver_status` → `_detect_frontend_port()` | **BLOCKED** — Bypass der Facade |
| `backend/tests/test_network_and_monitoring_status_v1.py` | `app.get_network_info()` | erlaubt (Legacy-Contract-Test) |
| `backend/tests/test_debug_instrumentation.py` | `get_network_info()` | erlaubt (Instrumentation) |
| `apps/dsi_radio/dsi_radio_qml.py` | `_get_network_info()` | **OUT_OF_SCOPE** (separates DSI-Radio-App) |

## HTTP-Routen-Matrix

| Route | Handler-Ort | Network-Zugriff |
|-------|-------------|-----------------|
| `GET /api/status` | `api/routes/network.py` | Facade only ✓ |
| `GET /api/system/network` | `api/routes/network.py` | Facade only ✓ |
| `GET /api/system-info` | `app.py` | Facade für `network`-Block |
| `GET /api/webserver/status` | `app.py` | Facade + direkter `_detect_frontend_port` |

## Frontend-Konsumenten (read-only)

| Endpoint | Frontend-Dateien |
|----------|------------------|
| `/api/system-info` | `App.tsx`, `Dashboard.tsx`, `MonitoringDashboard.tsx`, `InstallationWizard.tsx` |
| `/api/system/network` | `Dashboard.tsx`, `ControlCenter.tsx`, `SettingsPage.tsx`, `Sidebar.tsx` |
| `/api/webserver/status` | `WebServerSetup.tsx` |

## Stale-Metadaten

`system_status_facade.build_system_status_diagnostics()` listet noch `GET /api/status` unter `routes_pending_facade_migration` — veraltet seit G.4 (kein Network-Owner-Problem, aber Doku-Drift).

## Fazit

**Owner intakt:** Alle produktiven Network-HTTP-Pfade nutzen die Facade-API.  
**Legacy-Kette:** Implementierung bleibt in `app.py`; Facade importiert `app` lazy (zyklische Kopplung).  
**Ein Bypass:** `webserver_status` ruft `_detect_frontend_port` direkt auf.
