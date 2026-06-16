# System Info Audit — Phase G.6

**HEAD (Audit-Basis):** `23462c1` · **Datum:** 2026-06-10  
**Scope:** `GET /api/system-info` — Read-Only-Monolith-Entkopplung (STRICT MODE)

## Route

| Feld | Wert |
|------|------|
| **HTTP** | `GET /api/system-info` |
| **Query** | `light` (bool, default `false`) |
| **Demo** | Header `X-Demo-Mode: 1` → `use_demo=True` |
| **Handler vorher** | `backend/app.py` `get_system_info` (~240 Zeilen) |
| **Handler nachher** | Dünner Wrapper → `build_system_info()` |
| **Zeilen Handler** | 6 Zeilen (inkl. Decorator/Doku) |

## Aufrufer (Frontend)

| Datei | Aufruf |
|-------|--------|
| `frontend/src/App.tsx` | `/api/system-info` (PlatformContext) |
| `frontend/src/pages/Dashboard.tsx` | `/api/system-info?light=1` |
| `frontend/src/pages/MonitoringDashboard.tsx` | `/api/system-info?light=1` |
| `frontend/src/pages/InstallationWizard.tsx` | `/api/system-info?light=1` |

Keine Backend-internen Python-Aufrufer außer Route-Handler.

## Datenquellen

### Runtime (psutil / /proc)

| Quelle | Felder |
|--------|--------|
| `psutil.cpu_percent` | `cpu.usage`, `per_cpu_usage`, Kerne |
| `psutil.virtual_memory` | `memory.*` |
| `psutil.disk_usage('/')` | `disk.*` |
| `psutil.disk_partitions` | `disk.partition` |
| `/proc/uptime` | `uptime` |
| `/etc/os-release` + `uname -r` | `os.*`, `platform.*` |
| `/sys/class/thermal/thermal_zone0/temp` | `cpu.temperature` (light/fast) |

### Hardware (Legacy-Adapter → `app.py`)

| Helper | Response-Felder |
|--------|-----------------|
| `get_per_core_usage` | `cpu.per_core_usage`, `physical_cores` |
| `get_cpu_temp`, `get_fan_speed` | `cpu.temperature`, `fan_speed` |
| `get_cpu_name`, `get_cpu_summary` | `cpu_name`, `cpu_summary` |
| `_get_pi_config_module().get_system_info()` | `hardware`, `is_raspberry_pi` |
| `_get_gpus_for_system_info` | `hardware.gpus` (Non-Pi) |
| `get_motherboard_info`, `get_ram_info` | `motherboard`, `ram_info` |
| `get_all_thermal_sensors/disks/fans/displays` | `sensors`, `disks`, `fans`, `displays` |
| `_get_pci_with_drivers`, `_clean_gpu_description` | `drivers` |
| DMI `/sys/class/dmi/id/chassis_type` | `device_type` |
| Device-Tree `/proc/device-tree/model` | Pi-Fallback |

### Netzwerk (nur Facade)

| Owner | Funktion |
|-------|----------|
| `network_info_facade` | `build_network_info()` / `build_demo_network_info()` |
| **Entfernt** | Direkte `get_network_info` / `_demo_network` im Handler |

### DCC / Status-Taxonomie

| Owner | Nutzung |
|-------|---------|
| `dcc_status_facade.build_section_status` | `build_system_info_sections()` — runtime/hardware/network Sections |

Kein DCC-Aggregationsblock im Legacy-Payload; DCC konsumiert andere Endpoints.

## Abhängigkeiten

```
GET /api/system-info (app.py)
  └── system_info_facade.build_system_info(light, use_demo)
        ├── psutil, os, pathlib, open(/proc, /etc)
        ├── network_info_facade.build_network_info | build_demo_network_info
        ├── dcc_status_facade.build_section_status (sections API)
        └── Legacy-Adapter (lazy import app)
              ├── run_command, get_cpu_*, get_motherboard_info, …
              └── _get_pi_config_module
```

**Keine neuen subprocess-Aufrufe** in der Facade; `run_command` nur über Legacy-Adapter (bestehend).

## Response-Shape (unverändert)

### `light=true`

`os`, `cpu`, `memory`, `disk`, `platform`, `uptime`, optional `cpu_name`, `cpu_summary`, `app_edition` — **kein** `network`.

### Vollständig (`light=false`)

Zusätzlich: `is_raspberry_pi`, `device_type`, `hardware`, `motherboard`, `ram_info`, `manufacturer_driver_tip`, `sensors`, `disks`, `fans`, `displays`, `drivers`, `network`, `app_edition`.

Fehlerfall: `{"error": "<message>"}` (Legacy-kompatibel).

## Facade-Kandidaten / Ergebnis G.6

| Modul | Status |
|-------|--------|
| `backend/core/system_info_facade.py` | **CANONICAL** — `SYSTEM_INFO_FACADE_VERSION = 1` |
| Öffentliche API | `build_system_info`, `build_system_info_sections`, `build_hardware_section`, `build_runtime_section`, `build_network_section`, `build_system_info_diagnostics` |

## Metriken

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| `app.py` Handler-Zeilen | ~240 | 6 |
| `app.py` Gesamt | 16927 (nach G.7/G.8) | 16927 (−238 aus Handler) |
| Facade-Modul | — | 557 Zeilen |
| Direkte Network-Aufrufe im Handler | 0 (seit G.3) | 0 |
| Direkte Network-Logik in Facade | — | 0 (nur `network_info_facade`) |

## Verbleibende Legacy-Abhängigkeiten

- Hardware-Helfer in `app.py` (über `_legacy_*` Adapter)
- `psutil` und Dateilesen in Facade (extrahiert, nicht neu)
- `app._is_demo_mode(request)` bleibt im HTTP-Handler (Demo-Gate)

## Tests

- `backend/tests/test_system_info_facade_v1.py`
- `backend/tests/test_system_info_route_migration_g6.py`
- `backend/tests/test_network_info_core_cleanup_g3.py` (angepasst)

## Boundary Guards (G.6, WARN-only)

- `system_info_facade_missing`
- `system_info_route_requires_facade`
- `system_info_direct_network_usage`
- `system_info_duplicate_status_mapping`
- `system_info_new_logic_outside_facade`
- `system_info_facade_bypasses_network_facade`

Snapshot: `docs/evidence/app-monolith/BOUNDARY_WARNINGS_G6.txt`
