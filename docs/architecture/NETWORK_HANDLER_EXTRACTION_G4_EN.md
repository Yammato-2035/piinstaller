# Network Handler Extraction — G.4 (EN)

**HEAD:** after G.4 · **Status:** done

## Extracted routes

| Route | Module | Facade API |
|-------|--------|------------|
| `GET /api/status` | `api/routes/network.py` | `build_api_status_payload` |
| `GET /api/system/network` | `api/routes/network.py` | `build_system_network_response` |

## Blocked (remain in `app.py`)

| Route | Reason |
|-------|--------|
| `GET /api/system-info` | System info aggregation (psutil), not a pure network handler |
| `GET /api/webserver/status` | Webserver/service probes (`run_command`, `ss`) alongside facade `network` |

## Legacy remains

- `app.get_network_info`, `app._demo_network` — implementation behind facade adapters

## Tests

`backend/tests/test_network_router_extraction_g4.py`

## Boundary guards (warn-only)

- `network_router_extraction_g4_*`
- `app_network_handler_remaining`
- `network_router_bypasses_facade`
- `network_direct_usage_outside_facade`

## Next step

Further `app.py` router slices (E.9+) or dev-dashboard aggregation (E.7 candidates).
