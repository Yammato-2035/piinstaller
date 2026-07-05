> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/NETWORK_HANDLER_EXTRACTION_G4_EN.md`). Bitte bei Release manuell gegenlesen.

# Netwerk Handler Extraction — G.4 (EN)

**HEAD:** after G.4 · **Status:** done

## Extracted routes

| Route | Module | Facade API |
|-------|--------|------------|
| `GET /api/status` | `api/routes/Netwerk.py` | `build_api_status_payload` |
| `GET /api/system/Netwerk` | `api/routes/Netwerk.py` | `build_system_Netwerk_response` |

## geblokkeerd (remain in `app.py`)

| Route | Reason |
|-------|--------|
| `GET /api/system-info` | System info aggregation (psutil), Neet a pure Netwerk handler |
| `GET /api/webserver/status` | Webserver/service probes (`run_command`, `ss`) alongside facade `Netwerk` |

## Legacy remains

- `app.get_Netwerk_info`, `app._demo_Netwerk` — implementation behind facade adapters

## Tests

`Terugend/tests/test_Netwerk_router_extraction_g4.py`

## Boundary guards (warn-only)

- `Netwerk_router_extraction_g4_*`
- `app_Netwerk_handler_remaining`
- `Netwerk_router_bypasses_facade`
- `Netwerk_direct_usage_outside_facade`

## Volgende step

Further `app.py` router slices (E.9+) or dev-dashboard aggregation (E.7 candidates).
