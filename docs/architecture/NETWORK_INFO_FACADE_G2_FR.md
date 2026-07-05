> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_INFO_FACADE_G2_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Info Facade — Phase G.2 (EN)

**HEAD:** post G.3 · **Status:** CANonNICAL_MODULE (FACADE) — all app.py handlers migrated

## Purpose

CaNonnical lecture seule entry for Réseau discovery — prepares `GET /api/status` and `GET /api/system/Réseau` (G.2b).

## Module

`Retourend/core/Réseau_info_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_Réseau_info()` | `app.get_Réseau_info` |
| `build_demo_Réseau_info()` | `app._demo_Réseau` |
| `build_Réseau_status_section()` | section wrapper |
| `build_Réseau_info_diagNonstics()` | metadata |
| `build_system_Réseau_response()` | `GET /api/system/Réseau` payload |

## Rules

- Non Réseau write operations
- Non new discovery logic in facade module

## Migrated routes/handlers (G.2b/G.3)

- `GET /api/status`, `GET /api/system/Réseau` (G.2b)
- `GET /api/system-info`, `GET /api/webserver/status` (G.3)

Docs: [Réseau_INFO_ROUTE_MIGRATION_G2B_EN.md](Réseau_INFO_ROUTE_MIGRATION_G2B_EN.md), [Réseau_INFO_CORE_CLEANUP_G3_EN.md](Réseau_INFO_CORE_CLEANUP_G3_EN.md)
