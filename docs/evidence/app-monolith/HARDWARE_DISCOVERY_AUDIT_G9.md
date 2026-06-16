# Hardware Discovery Audit — Phase G.9

**HEAD (Audit-Basis):** uncommitted G.6+G.9 workspace · **Datum:** 2026-06-10  
**Scope:** Facade→app-Zyklus für `system_info_facade` beseitigen

## Ausgangslage (G.6)

`system_info_facade.py` nutzte **17 `_legacy_*` Adapter** mit lazy `import app` für Hardware-/System-Discovery.

## Inventar — entfernte Adapter

| Adapter | app.py-Funktion | Discovery-Owner (G.9) |
|---------|-----------------|------------------------|
| `_legacy_run_command` | `run_command` | `hardware_discovery.run_command` / `_shell_run` |
| `_legacy_get_per_core_usage` | `get_per_core_usage` | `discover_cpu_info` |
| `_legacy_get_cpu_temp` | `get_cpu_temp` | `discover_cpu_info` |
| `_legacy_get_fan_speed` | `get_fan_speed` | `discover_cpu_info` |
| `_legacy_get_cpu_name` | `get_cpu_name` | `discover_cpu_info` |
| `_legacy_get_cpu_summary` | `get_cpu_summary` | `discover_cpu_info` |
| `_legacy_get_app_edition` | `get_app_edition` | `_resolve_app_edition()` in Facade (env only) |
| `_legacy_get_pi_config_module` | `_get_pi_config_module` | `discover_raspberry_pi_info` |
| `_legacy_get_gpus_for_system_info` | `_get_gpus_for_system_info` | `discover_pci_info` |
| `_legacy_get_motherboard_info` | `get_motherboard_info` | `discover_mainboard_info` |
| `_legacy_get_ram_info` | `get_ram_info` | `discover_memory_info` |
| `_legacy_get_all_thermal_sensors` | `get_all_thermal_sensors` | `discover_sensor_info` |
| `_legacy_get_all_disks` | `get_all_disks` | `discover_sensor_info` |
| `_legacy_get_all_fans` | `get_all_fans` | `discover_sensor_info` |
| `_legacy_get_all_displays` | `get_all_displays` | `discover_sensor_info` |
| `_legacy_get_pci_with_drivers` | `_get_pci_with_drivers` | `discover_pci_info` |
| `_legacy_clean_gpu_description` | `_clean_gpu_description` | `discover_pci_info` |

## Datenquellen (unverändert, extrahiert)

| Bereich | Inputs | Outputs | Seiteneffekte |
|---------|--------|---------|---------------|
| CPU | `/proc/cpuinfo`, `lscpu`, thermal sysfs, `vcgencmd`, `sensors` | name, summary, temp, fan, per-core usage | read-only |
| RAM | `dmidecode -t memory`, DMI sysfs | RAM-Modul-Liste | read-only subprocess |
| Mainboard | DMI sysfs, `dmidecode -t baseboard` | vendor/name/product | read-only |
| PCI/GPU | `lspci -k`, `nvidia-smi`, Codename-Map | pci_list, gpus, drivers | read-only subprocess |
| Sensoren | thermal_zone, hwmon, psutil disks, `xrandr` | sensors, disks, fans, displays | read-only |
| Raspberry Pi | `RaspberryPiConfigModule`, device-tree model | hardware cpus/gpus, is_raspberry_pi | read-only |

**Keine neuen subprocess-Aufrufe** — bestehende Probes über `_shell_run` (wie G.8 `network_discovery`).

## Aufrufer

| Konsument | Nach G.9 |
|-----------|----------|
| `system_info_facade.build_system_info` | `hardware_discovery.discover_*` |
| `app.py` Legacy-API | dünne Wrapper → `hardware_discovery` |
| `GET /api/system-info` | unverändert (Facade only) |

## Legacy-Ketten (nachher)

```
GET /api/system-info
  └── system_info_facade.build_system_info
        ├── hardware_discovery.discover_*   (G.9 — kein app-Import)
        ├── network_info_facade             (G.6/G.8)
        └── psutil / open(/proc)            (Runtime, unverändert)

app.get_cpu_temp / … (andere Caller)
  └── hardware_discovery.<fn>   (Wrapper, G.9)
```

## Metriken

| Modul | Zeilen |
|-------|--------|
| `hardware_discovery.py` | ~873 |
| `system_info_facade.py` | ~460 (−97 Adapter) |
| `app.py` Hardware-Funktionen | je ~5 Zeilen Wrapper |

## Tests

- `test_hardware_discovery_v1.py`
- `test_system_info_without_app_dependency_g9.py`
- `test_system_info_facade_v1.py` (angepasst)

## Boundary Guards (G.9)

`hardware_discovery_core_missing`, `system_info_facade_depends_on_app`, `hardware_legacy_wrapper_missing`, `hardware_new_logic_outside_discovery`, `hardware_direct_discovery_usage_outside_facade`

Snapshot: `docs/evidence/app-monolith/BOUNDARY_WARNINGS_G9.txt`
