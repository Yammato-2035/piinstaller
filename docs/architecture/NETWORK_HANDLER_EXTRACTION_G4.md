# Network Handler Extraction — G.4

**HEAD:** nach G.4 · **Status:** erledigt

## Extrahierte Routen

| Route | Modul | Facade-API |
|-------|-------|------------|
| `GET /api/status` | `api/routes/network.py` | `build_api_status_payload` |
| `GET /api/system/network` | `api/routes/network.py` | `build_system_network_response` |

## Blockiert (bleiben in `app.py`)

| Route | Grund |
|-------|-------|
| `GET /api/system-info` | Systeminfo-Aggregation (psutil), nicht reiner Network-Handler |
| `GET /api/webserver/status` | Webserver/Service-Probes (`run_command`, `ss`) neben Facade-`network` |

## Legacy bleibt

- `app.get_network_info`, `app._demo_network` — Implementierung hinter Facade-Adaptern

## Tests

`backend/tests/test_network_router_extraction_g4.py`

## Boundary-Guards (warn-only)

- `network_router_extraction_g4_*`
- `app_network_handler_remaining`
- `network_router_bypasses_facade`
- `network_direct_usage_outside_facade`

## Nächster Schritt

Weitere `app.py` Router-Slices (E.9+) oder Dev-Dashboard-Aggregation (E.7 Kandidaten).
