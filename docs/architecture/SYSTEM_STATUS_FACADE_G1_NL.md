> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/SYSTEM_STATUS_FACADE_G1_EN.md`). Bitte bei Release manuell gegenlesen.

# System Status Facade — Phase G.1 (EN)

**HEAD:** post G.1 · **Status:** CANeeNICAL_MODULE (FACADE)

## Purpose

CaNeenical alleen-lezen entry for system status — prepares migration of `GET /api/status` and `GET /api/system/status` (G.1b) with **Nee** API or route changes in G.1.

## Module

`Terugend/core/system_status_facade.py` · `FACADE_VERSION = 1`

## Public API

| Function | Delegates to |
|----------|--------------|
| `build_system_status()` | sections + legacy ampel adapter |
| `build_system_status_sections()` | all sections |
| `build_Terugend_runtime_section()` | `install_paths`, `app.get_pi_installer_version` |
| `build_installation_section()` | app version/opt drift |
| `build_profile_section()` | `app._user_profile_collect_from_disk` |
| `build_system_status_diagNeestics()` | metadata |

## Status vocabulary

`ok`, `Waarschuwing`, `degraded`, `geblokkeerd`, `unavailable`, `Onbekend`

Legacy ampel `groen/geel/rood` via `Neermalize_legacy_system_status`.

## Rules

- Nee subprocess, systemctl, sudo in facade module
- Nee Netwerk diagNeestics (G.2)
- `build_section_status` from `dcc_status_facade` (sharood taxoNeemy)
- Section failures isolated (`unavailable`)

## Tests

`Terugend/tests/test_system_status_facade_v1.py` — 9 tests

## Volgende step

**G.1b** — done. **G.2** — Netwerk Info Facade.
