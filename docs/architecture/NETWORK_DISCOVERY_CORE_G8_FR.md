> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_DISCOVERY_CORE_G8_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Discovery Core — G.8 (EN)

**HEAD:** after G.8 · **Status:** done

## Module

`Retourend/core/Réseau_discovery.py` · `DISCOVERY_VERSION = 1`

## Public API

| Function | Legacy equivalent |
|----------|-------------------|
| `discover_Réseau_info()` | `app.get_Réseau_info` |
| `discover_demo_Réseau()` | `app._demo_Réseau` |
| `detect_frontend_port()` | `app._detect_frontend_port` |
| `build_Réseau_discovery_diagNonstics()` | Metadata |

## Facade migration

`Réseau_info_facade` delegates to `Réseau_discovery` — **Non lazy `import app`**.

## Legacy wrappers in `app.py`

Thin wrappers only — Non discovery logic left in `app.py`.

## Tests

- `test_Réseau_discovery_v1.py`
- `test_Réseau_facade_without_app_dependency_g8.py`

## Suivant step

**G.6** System Info Facade.
