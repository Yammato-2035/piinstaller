# Network Info Core Cleanup — G.3

**HEAD:** nach G.3 · **Status:** erledigt

## Migrierte Funktionen

| Handler | Facade |
|---------|--------|
| `get_system_info` | `build_network_info` / `build_demo_network_info` |
| `webserver_status` | `build_network_info` |

## Legacy bleibt

- `app.get_network_info` — Implementierung (subprocess/ip)
- `app._demo_network` — Demo-Platzhalter
- Facade `_legacy_*` Adapter

## Tests

`backend/tests/test_network_info_core_cleanup_g3.py`

## Nächster Schritt

**H.1** Frontend Status ViewModel Facade oder **G.4** Network Handler Extraction
