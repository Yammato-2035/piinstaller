# Network Info Facade — Phase G.2 (EN)

**HEAD:** post G.2 · **Status:** CANONICAL_MODULE (FACADE)

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
| `normalize_legacy_network_info()` | facade status |

## Rules

- No network write operations
- No new discovery logic in facade module

## Next step

**G.2b** — migrate `GET /api/status` and `GET /api/system/network` routes
