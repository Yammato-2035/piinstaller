> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/NETWORK_HANDLER_EXTRACTION_G4_EN.md`). Bitte bei Release manuell gegenlesen.

# Réseau Handler Extraction — G.4 (EN)

**HEAD:** after G.4 · **Status:** done

## Extracted routes

| Route | Module | Facade API |
|-------|--------|------------|
| `GET /api/status` | `api/routes/Réseau.py` | `build_api_status_payload` |
| `GET /api/system/Réseau` | `api/routes/Réseau.py` | `build_system_Réseau_response` |

## bloqué (remain in `app.py`)

| Route | Reason |
|-------|--------|
| `GET /api/system-info` | System info aggregation (psutil), Nont a pure Réseau handler |
| `GET /api/webserver/status` | Webserver/service probes (`run_command`, `ss`) alongside facade `Réseau` |

## Legacy remains

- `app.get_Réseau_info`, `app._demo_Réseau` — implementation behind facade adapters

## Tests

`Retourend/tests/test_Réseau_router_extraction_g4.py`

## Boundary guards (warn-only)

- `Réseau_router_extraction_g4_*`
- `app_Réseau_handler_remaining`
- `Réseau_router_bypasses_facade`
- `Réseau_direct_usage_outside_facade`

## Suivant step

Further `app.py` router slices (E.9+) or dev-dashboard aggregation (E.7 candidates).
