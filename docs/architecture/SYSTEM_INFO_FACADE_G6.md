# System Info Facade — G.6

**HEAD:** nach G.6 · **Status:** erledigt

## Modul

`backend/core/system_info_facade.py` · `SYSTEM_INFO_FACADE_VERSION = 1`

## Öffentliche API

| Funktion | Zweck |
|----------|-------|
| `build_system_info()` | Legacy `GET /api/system-info` Payload |
| `build_system_info_sections()` | Section-Wrapper (`build_section_status`) |
| `build_hardware_section()` | Hardware-Slice |
| `build_runtime_section()` | Runtime-Slice (os/cpu/memory/disk) |
| `build_network_section()` | Network-Block über `network_info_facade` |
| `build_system_info_diagnostics()` | Metadaten |

## Delegation

| Bereich | Owner |
|---------|-------|
| Network | `network_info_facade.build_network_info` / `build_demo_network_info` |
| Status-Sections | `dcc_status_facade.build_section_status` |
| Hardware/Services | Legacy-Adapter → `app.*` |
| Runtime psutil | Extrahiert in Facade (keine neue Logik) |

## Migration

| Route | Vorher | Nachher |
|-------|--------|---------|
| `GET /api/system-info` | ~240 Zeilen in `app.py` | `build_system_info(light, use_demo)` |

**G.3→G.6:** Network-Block im Handler war bereits Facade-only (G.3); G.6 extrahiert den gesamten Handler.

## Tests

- `test_system_info_facade_v1.py`
- `test_system_info_route_migration_g6.py`

## Nächster Schritt

Monolith-Slices: verbleibende `app.py` GET-Routen gemäß Roadmap (E.x / weitere G-Phasen).
