# Network Info Facade — Phase G.2 (EN)

**HEAD:** post G.3 · **Status:** CANONICAL_MODULE (FACADE) — all app.py handlers migrated

## Purpose

Canonical read-only entry for network discovery — prepares `GET /api/status` and `GET /api/system/network` (G.2b).

## Module

`backend/core/network_info_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_network_info()` | `app.get_network_info` |
| `build_demo_network_info()` | `app._demo_network` |
| `build_network_status_section()` | section wrapper |
| `build_network_info_diagnostics()` | metadata |
| `build_system_network_response()` | `GET /api/system/network` payload |

## Rules

- No network write operations
- No new discovery logic in facade module

## Migrated routes/handlers (G.2b/G.3)

- `GET /api/status`, `GET /api/system/network` (G.2b)
- `GET /api/system-info`, `GET /api/webserver/status` (G.3)

Docs: [NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md](NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md), [NETWORK_INFO_CORE_CLEANUP_G3_EN.md](NETWORK_INFO_CORE_CLEANUP_G3_EN.md)
