# Network Handler Extraction Audit — G.4

**HEAD vorher:** `d113bdb`  
**Branch:** `main`  
**Phase 0:** `./scripts/check-module-boundaries.sh` Exit 0 (review_required)

## Inventar (GET)

| Route | Vorher (`app.py`) | G.4 Entscheidung | Begründung |
|-------|-------------------|------------------|------------|
| `GET /api/status` | `get_status` → Facade | **extrahiert** | Reine Facade-Delegation |
| `GET /api/system/network` | `get_system_network` → Facade | **extrahiert** | Reine Facade-Delegation + Logging |
| `GET /api/system-info` | `get_system_info` (psutil/CPU/Disk) | **blocked** | Kein Network-Handler; ~240 Zeilen Systeminfo |
| `GET /api/webserver/status` | `webserver_status` | **blocked** | `run_command`/`ss`, `get_running_services`, nicht Facade-only |

**Hinweis:** Auftrag nennt `GET /api/system/info` — kanonischer Pfad ist `GET /api/system-info` (Bindestrich).

## Verbleibende Network-Bezüge in `app.py`

| Symbol | Rolle |
|--------|-------|
| `get_network_info` | Legacy-Discovery (subprocess/ip) — Facade-Adapter |
| `_demo_network` | Demo-Platzhalter — Facade-Adapter |
| `get_system_info` | HTTP-Handler; `network`-Block via Facade |
| `webserver_status` | HTTP-Handler; `network` via Facade, Rest app-Helfer |

## Neues Modul

- `backend/api/routes/network.py` — `include_router(network_router)` in `app.py`
- Facade-Ergänzung: `build_api_status_payload`

## Metriken

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| `app.py` Zeilen | 17380 | 17338 (−42) |
| Network-GET in Router | 0 | 2 |
| Network-GET in `app.py` | 2 | 0 |

## Tests

- `backend/tests/test_network_router_extraction_g4.py` (neu)
- `test_network_info_route_migration_g2b.py` (Router-Quelle)
- `test_network_info_core_cleanup_g3.py` (blocked Handler)
- `test_network_info_facade_v1.py` (`build_api_status_payload`)
- `test_system_status_route_migration_g1b.py` (Status-Router-Move)

Keine Runtime-Smokes.
