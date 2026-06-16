# Hardware Discovery Core — G.9

**Status:** erledigt

## Modul

`backend/core/hardware_discovery.py` · `HARDWARE_DISCOVERY_VERSION = 1`

## Öffentliche API

| Funktion | Zweck |
|----------|-------|
| `discover_cpu_info()` | CPU name/summary/temp/fan/per-core |
| `discover_memory_info()` | RAM-Module (dmidecode) |
| `discover_mainboard_info()` | DMI Baseboard |
| `discover_pci_info()` | lspci + GPUs + clean_gpu |
| `discover_sensor_info()` | thermal, disks, fans, displays |
| `discover_raspberry_pi_info()` | Pi-Modul + device-tree |
| `build_hardware_discovery_diagnostics()` | Metadaten |

## Migration

| Vorher (G.6) | Nachher (G.9) |
|--------------|---------------|
| `system_info_facade` → `_legacy_*` → `app.py` | `system_info_facade` → `hardware_discovery` |
| Hardware-Logik in `app.py` | Extrahiert nach `hardware_discovery` |
| `app.py` | Dünne Legacy-Wrapper |

**Zyklus beseitigt:** `system_info_facade` importiert `app` nicht mehr.

## Tests

- `test_hardware_discovery_v1.py`
- `test_system_info_without_app_dependency_g9.py`

## Nächster Schritt

Weitere `app.py` Monolith-Slices gemäß Roadmap (E.x).
