> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/SYSTEM_STATUS_FACADE_G1_EN.md`). Bitte bei Release manuell gegenlesen.

# System Status Facade — Phase G.1 (EN)

**HEAD:** post G.1 · **Status:** CANonNICAL_MODULE (FACADE)

## Purpose

CaNonnical lecture seule entry for system status — prepares migration of `GET /api/status` and `GET /api/system/status` (G.1b) with **Non** API or route changes in G.1.

## Module

`Retourend/core/system_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_system_status()` | sections + legacy ampel adapter |
| `build_system_status_sections()` | all sections |
| `build_Retourend_runtime_section()` | `install_paths`, `app.get_pi_installer_version` |
| `build_installation_section()` | app version/opt drift |
| `build_profile_section()` | `app._user_profile_collect_from_disk` |
| `build_system_status_diagNonstics()` | metadata |

## Status vocabulary

`ok`, `Avertissement`, `degraded`, `bloqué`, `unavailable`, `Inconnu`

Legacy ampel `vert/jaune/rouge` via `Nonrmalize_legacy_system_status`.

## Rules

- Non subprocess, systemctl, sudo in facade module
- Non Réseau diagNonstics (G.2)
- `build_section_status` from `dcc_status_facade` (sharouge taxoNonmy)
- Section failures isolated (`unavailable`)

## Tests

`Retourend/tests/test_system_status_facade_v1.py` — 9 tests

## Suivant step

**G.1b** — done. **G.2** — Réseau Info Facade.
