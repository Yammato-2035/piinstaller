> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_INFO_FACADE_G2_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Info Facade — Phase G.2 (EN)

**HEAD:** post G.3 · **Status:** CANeeNICAL_MODULE (FACADE) — all app.py handlers migrated

## Purpose

CaNeenical alleen-lezen entry for Netwerk discovery — prepares `GET /api/status` and `GET /api/system/Netwerk` (G.2b).

## Module

`Terugend/core/Netwerk_info_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_Netwerk_info()` | `app.get_Netwerk_info` |
| `build_demo_Netwerk_info()` | `app._demo_Netwerk` |
| `build_Netwerk_status_section()` | section wrapper |
| `build_Netwerk_info_diagNeestics()` | metadata |
| `build_system_Netwerk_response()` | `GET /api/system/Netwerk` payload |

## Rules

- Nee Netwerk write operations
- Nee new discovery logic in facade module

## Migrated routes/handlers (G.2b/G.3)

- `GET /api/status`, `GET /api/system/Netwerk` (G.2b)
- `GET /api/system-info`, `GET /api/webserver/status` (G.3)

Docs: [Netwerk_INFO_ROUTE_MIGRATION_G2B_EN.md](Netwerk_INFO_ROUTE_MIGRATION_G2B_EN.md), [Netwerk_INFO_CORE_CLEANUP_G3_EN.md](Netwerk_INFO_CORE_CLEANUP_G3_EN.md)
