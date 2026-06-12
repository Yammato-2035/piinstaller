# Network Info Facade — Phase G.2 (EN)

**HEAD:** post G.2b · **Status:** CANONICAL_MODULE (FACADE) — routes migrated

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

## Migrated routes (G.2b)

- `GET /api/status` — network block
- `GET /api/system/network` — full response

Doc: [NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md](NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md)
