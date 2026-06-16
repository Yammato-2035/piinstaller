# Hardware Discovery Core — G.9

**Status:** done

## Module

`backend/core/hardware_discovery.py` · `HARDWARE_DISCOVERY_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `discover_cpu_info()` | CPU name/summary/temp/fan/per-core |
| `discover_memory_info()` | RAM modules (dmidecode) |
| `discover_mainboard_info()` | DMI baseboard |
| `discover_pci_info()` | lspci + GPUs + clean_gpu |
| `discover_sensor_info()` | thermal, disks, fans, displays |
| `discover_raspberry_pi_info()` | Pi module + device-tree |
| `build_hardware_discovery_diagnostics()` | Metadata |

## Migration

| Before (G.6) | After (G.9) |
|--------------|-------------|
| `system_info_facade` → `_legacy_*` → `app.py` | `system_info_facade` → `hardware_discovery` |
| Hardware logic in `app.py` | Extracted to `hardware_discovery` |
| `app.py` | Thin legacy wrappers |

**Cycle broken:** `system_info_facade` no longer imports `app`.

## Tests

- `test_hardware_discovery_v1.py`
- `test_system_info_without_app_dependency_g9.py`

## Next step

Further `app.py` monolith slices per roadmap (E.x).
