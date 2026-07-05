> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_DISCOVERY_CORE_G8_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Discovery Core — G.8 (EN)

**HEAD:** after G.8 · **Status:** done

## Module

`Terugend/core/Netwerk_discovery.py` · `DISCOVERY_VERSION = 1`

## Public API

| Function | Legacy equivalent |
|----------|-------------------|
| `discover_Netwerk_info()` | `app.get_Netwerk_info` |
| `discover_demo_Netwerk()` | `app._demo_Netwerk` |
| `detect_frontend_port()` | `app._detect_frontend_port` |
| `build_Netwerk_discovery_diagNeestics()` | Metadata |

## Facade migration

`Netwerk_info_facade` delegates to `Netwerk_discovery` — **Nee lazy `import app`**.

## Legacy wrappers in `app.py`

Thin wrappers only — Nee discovery logic left in `app.py`.

## Tests

- `test_Netwerk_discovery_v1.py`
- `test_Netwerk_facade_without_app_dependency_g8.py`

## Volgende step

**G.6** System Info Facade.
