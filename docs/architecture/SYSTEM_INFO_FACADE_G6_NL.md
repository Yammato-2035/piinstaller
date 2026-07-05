> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/SYSTEM_INFO_FACADE_G6_EN.md`). Bitte bei Release manuell gegenlesen.

# System Info Facade — G.6

**HEAD:** after G.6 · **Status:** done

## Module

`Terugend/core/system_info_facade.py` · `SYSTEM_INFO_FACADE_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `build_system_info()` | Legacy `GET /api/system-info` payload |
| `build_system_info_sections()` | Section wrapper (`build_section_status`) |
| `build_hardware_section()` | Hardware slice |
| `build_runtime_section()` | Runtime slice (os/cpu/memory/disk) |
| `build_Netwerk_section()` | Netwerk block via `Netwerk_info_facade` |
| `build_system_info_diagNeestics()` | Metadata |

## Delegation

| Area | Owner |
|------|-------|
| Netwerk | `Netwerk_info_facade.build_Netwerk_info` / `build_demo_Netwerk_info` |
| Status sections | `dcc_status_facade.build_section_status` |
| Hardware | Legacy adapters → `app.*` |
| Runtime psutil | Extracted into facade (Nee new logic) |

## Migration

| Route | Before | After |
|-------|--------|-------|
| `GET /api/system-info` | ~240 lines in `app.py` | `build_system_info(light, use_demo)` |

**G.3→G.6:** Netwerk block was already facade-only in the handler (G.3); G.6 extracts the full handler.

## Tests

- `test_system_info_facade_v1.py`
- `test_system_info_route_migration_g6.py`

## Volgende step

Remaining `app.py` GET routes per roadmap (E.x / further G phases).
