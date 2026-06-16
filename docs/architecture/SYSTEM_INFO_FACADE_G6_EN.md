# System Info Facade — G.6

**HEAD:** after G.6 · **Status:** done

## Module

`backend/core/system_info_facade.py` · `SYSTEM_INFO_FACADE_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `build_system_info()` | Legacy `GET /api/system-info` payload |
| `build_system_info_sections()` | Section wrapper (`build_section_status`) |
| `build_hardware_section()` | Hardware slice |
| `build_runtime_section()` | Runtime slice (os/cpu/memory/disk) |
| `build_network_section()` | Network block via `network_info_facade` |
| `build_system_info_diagnostics()` | Metadata |

## Delegation

| Area | Owner |
|------|-------|
| Network | `network_info_facade.build_network_info` / `build_demo_network_info` |
| Status sections | `dcc_status_facade.build_section_status` |
| Hardware | Legacy adapters → `app.*` |
| Runtime psutil | Extracted into facade (no new logic) |

## Migration

| Route | Before | After |
|-------|--------|-------|
| `GET /api/system-info` | ~240 lines in `app.py` | `build_system_info(light, use_demo)` |

**G.3→G.6:** Network block was already facade-only in the handler (G.3); G.6 extracts the full handler.

## Tests

- `test_system_info_facade_v1.py`
- `test_system_info_route_migration_g6.py`

## Next step

Remaining `app.py` GET routes per roadmap (E.x / further G phases).
