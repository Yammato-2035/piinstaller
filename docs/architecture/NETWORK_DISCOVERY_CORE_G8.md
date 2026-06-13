# Network Discovery Core — G.8

**HEAD:** nach G.8 · **Status:** erledigt

## Modul

`backend/core/network_discovery.py` · `DISCOVERY_VERSION = 1`

## Öffentliche API

| Funktion | Legacy-Äquivalent |
|----------|-------------------|
| `discover_network_info()` | `app.get_network_info` |
| `discover_demo_network()` | `app._demo_network` |
| `detect_frontend_port()` | `app._detect_frontend_port` |
| `build_network_discovery_diagnostics()` | Metadaten |

## Facade-Migration

`network_info_facade` delegiert an `network_discovery` — **kein lazy `import app` mehr**.

## Legacy-Wrapper in `app.py`

| Wrapper | Delegation |
|---------|------------|
| `get_network_info()` | `discover_network_info()` |
| `_demo_network()` | `discover_demo_network()` |
| `_detect_frontend_port()` | `detect_frontend_port()` |

Keine eigene Discovery-Logik mehr in `app.py`.

## Tests

- `test_network_discovery_v1.py`
- `test_network_facade_without_app_dependency_g8.py`

## Nächster Schritt

**G.6** System Info Facade.
