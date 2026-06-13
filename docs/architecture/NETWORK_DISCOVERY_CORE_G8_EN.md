# Network Discovery Core — G.8 (EN)

**HEAD:** after G.8 · **Status:** done

## Module

`backend/core/network_discovery.py` · `DISCOVERY_VERSION = 1`

## Public API

| Function | Legacy equivalent |
|----------|-------------------|
| `discover_network_info()` | `app.get_network_info` |
| `discover_demo_network()` | `app._demo_network` |
| `detect_frontend_port()` | `app._detect_frontend_port` |
| `build_network_discovery_diagnostics()` | Metadata |

## Facade migration

`network_info_facade` delegates to `network_discovery` — **no lazy `import app`**.

## Legacy wrappers in `app.py`

Thin wrappers only — no discovery logic left in `app.py`.

## Tests

- `test_network_discovery_v1.py`
- `test_network_facade_without_app_dependency_g8.py`

## Next step

**G.6** System Info Facade.
