# System Status Facade — Phase G.1 (EN)

**HEAD:** post G.1 · **Status:** CANONICAL_MODULE (FACADE)

## Purpose

Canonical read-only entry for system status — prepares migration of `GET /api/status` and `GET /api/system/status` (G.1b) with **no** API or route changes in G.1.

## Module

`backend/core/system_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_system_status()` | sections + legacy ampel adapter |
| `build_system_status_sections()` | all sections |
| `build_backend_runtime_section()` | `install_paths`, `app.get_pi_installer_version` |
| `build_installation_section()` | app version/opt drift |
| `build_profile_section()` | `app._user_profile_collect_from_disk` |
| `build_system_status_diagnostics()` | metadata |

## Status vocabulary

`ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`

Legacy ampel `green/yellow/red` via `normalize_legacy_system_status`.

## Rules

- No subprocess, systemctl, sudo in facade module
- No network diagnostics (G.2)
- `build_section_status` from `dcc_status_facade` (shared taxonomy)
- Section failures isolated (`unavailable`)

## Tests

`backend/tests/test_system_status_facade_v1.py` — 9 tests

## Next step

**G.1b** — done. **G.2** — Network Info Facade.
