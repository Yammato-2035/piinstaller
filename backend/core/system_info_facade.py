"""
System Info Facade — canonical read-only aggregation for GET /api/system-info.

Phase G.6: contract + delegation only; route response shape unchanged.
Delegates hardware/runtime helpers to legacy ``app`` adapters.
Network via ``network_info_facade`` only — no direct discovery.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

import psutil

from core.dcc_status_facade import build_section_status
from core.hardware_discovery import (
    build_hardware_discovery_diagnostics,
    discover_cpu_info,
    discover_mainboard_info,
    discover_memory_info,
    discover_pci_info,
    discover_raspberry_pi_info,
    discover_sensor_info,
    run_command,
)
from core.network_info_facade import build_demo_network_info, build_network_info

SYSTEM_INFO_FACADE_VERSION = 1

FACADE_STATUS_VALUES = frozenset(
    {
        "ok",
        "warning",
        "degraded",
        "blocked",
        "unavailable",
        "unknown",
    }
)


@dataclass(frozen=True)
class SystemInfoFacadeWarning:
    code: str
    message: str
    section: str | None = None


@dataclass
class SystemInfoSection:
    section_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _warning(code: str, message: str, section: str | None = None) -> SystemInfoFacadeWarning:
    return SystemInfoFacadeWarning(code=code, message=message, section=section)


def build_unavailable_system_info_section(section_id: str, *, reason: str) -> SystemInfoSection:
    return SystemInfoSection(
        section_id=section_id,
        status="unavailable",
        data={},
        errors=[reason],
        warnings=[reason],
    )


def _safe_section(
    section_id: str,
    builder: Callable[[], SystemInfoSection],
    *,
    facade_warnings: list[SystemInfoFacadeWarning],
    facade_errors: list[str],
) -> SystemInfoSection:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001
        msg = f"{section_id}_failed:{exc}"
        facade_errors.append(msg)
        facade_warnings.append(_warning(f"{section_id}_unavailable", msg, section_id))
        return build_unavailable_system_info_section(section_id, reason=msg)


def _resolve_app_edition() -> str:
    """App edition from environment (legacy ``get_app_edition`` shape, no app import)."""
    raw = (os.environ.get("APP_EDITION") or "").strip().lower()
    if raw in ("repo", "release"):
        return raw
    return "release"


def build_network_section(*, use_demo: bool = False) -> dict[str, Any]:
    """Network block via canonical network_info_facade (G.6)."""
    info = build_demo_network_info() if use_demo else build_network_info()
    return info if isinstance(info, dict) else {}


def build_runtime_section(*, light: bool = False) -> dict[str, Any]:
    """Runtime slice (os/cpu/memory/disk/platform/uptime) from full payload."""
    payload = build_system_info(light=light, use_demo=False)
    keys = ("os", "cpu", "memory", "disk", "platform", "uptime", "cpu_name", "cpu_summary", "app_edition")
    return {k: payload[k] for k in keys if k in payload}


def build_hardware_section(*, use_demo: bool = False) -> dict[str, Any]:
    """Hardware slice from full payload."""
    payload = build_system_info(light=False, use_demo=use_demo)
    keys = (
        "is_raspberry_pi",
        "device_type",
        "hardware",
        "motherboard",
        "ram_info",
        "manufacturer_driver_tip",
        "sensors",
        "disks",
        "fans",
        "displays",
        "drivers",
    )
    return {k: payload[k] for k in keys if k in payload}


def build_system_info(*, light: bool = False, use_demo: bool = False) -> dict[str, Any]:
    """Legacy ``GET /api/system-info`` payload (G.6)."""
    try:
        # light-Modus: kurzes interval (0.2s) für aktuelle Werte, ohne 1s zu blockieren. Sonst: 1s.
        cpu_interval = 0.2 if light else 1
        per_cpu_percent = psutil.cpu_percent(interval=cpu_interval, percpu=True)
        cpu_percent = sum(per_cpu_percent) / len(per_cpu_percent) if per_cpu_percent else 0
        cpu_probe: dict[str, Any] = {}
        if light:
            per_core_usage, physical_cores = [], 0
        else:
            cpu_probe = discover_cpu_info(per_cpu_percent=per_cpu_percent)
            per_core_usage = cpu_probe.get("per_core_usage", [])
            physical_cores = int(cpu_probe.get("physical_cores") or 0)
        # Fallback: psutil.cpu_count(logical=False) wenn physical_cores 0 ist
        if physical_cores == 0:
            try:
                physical_cores = psutil.cpu_count(logical=False) or 0
            except Exception:
                physical_cores = 0
        # Weitere Fallback: Bei 0 Kerne (z. B. unter Linux oft None) aus Threads schätzen
        if physical_cores == 0 and per_cpu_percent:
            try:
                physical_cores = max(1, len(per_cpu_percent) // 2)
            except Exception:
                pass
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        disk_mountpoint = '/'
        disk_partition = ''
        for p in psutil.disk_partitions(all=False):
            if p.mountpoint == '/':
                disk_partition = p.device.rstrip('/').split('/')[-1] or p.device
                break
        
        # Uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime = f"{hours}h {minutes}m"
        
        # CPU Temperatur: light nur schneller sysfs-Lese, sonst voller Weg
        cpu_temp = None
        temp_debug = None
        if light:
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
            except Exception:
                pass
        else:
            cpu_temp = cpu_probe.get("temperature")
            try:
                temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
                if temp_path.exists():
                    temp_debug = int(temp_path.read_text().strip()) / 1000.0
            except Exception:
                pass
        fan_speed = None if light else cpu_probe.get("fan_speed")
        
        fan_debug = None
        # Linux-Version (light: minimal)
        os_info = {}
        try:
            # /etc/os-release lesen
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        value = value.strip('"')
                        os_info[key.lower()] = value
            
            # Kernel-Version
            kernel_result = run_command("uname -r")
            os_info["kernel"] = kernel_result.get("stdout", "").strip() if kernel_result["success"] else "Unbekannt"
        except:
            os_info = {"name": "Unbekannt", "version": "Unbekannt", "kernel": "Unbekannt"}
        
        resp = {
            "os": {
                "name": os_info.get("pretty_name", os_info.get("name", "Linux")),
                "version": os_info.get("version_id", os_info.get("version", "")),
                "kernel": os_info.get("kernel", "Unbekannt"),
            },
            "cpu": {
                "usage": cpu_percent,
                "per_cpu_usage": per_cpu_percent,
                "per_core_usage": per_core_usage,
                "physical_cores": physical_cores,
                "count": psutil.cpu_count(),
                "thread_count": psutil.cpu_count(),
                "temperature": cpu_temp or temp_debug,
                "fan_speed": fan_speed,
                "temp_debug": temp_debug,
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "mountpoint": disk_mountpoint,
                "partition": disk_partition,
            },
            "platform": {
                "system": os.uname().sysname,
                "release": os.uname().release,
            },
            "uptime": uptime,
        }
        if light:
            # Light-Response: cpu_summary und cpu_name mitliefern, damit Dashboard Kerne/Threads anzeigen kann
            cpu_light = discover_cpu_info()
            _cpu_name = cpu_light.get("name")
            if _cpu_name:
                resp["cpu_name"] = _cpu_name
            _cs = dict(cpu_light.get("summary") or {})
            _cs["name"] = _cs.get("name") or _cpu_name
            if resp.get("cpu", {}).get("physical_cores"):
                _cs["cores"] = _cs.get("cores") or resp["cpu"]["physical_cores"]
            if not _cs.get("cores") and resp.get("cpu", {}).get("count"):
                _cs["cores"] = max(1, resp["cpu"]["count"] // 2)
            if resp.get("cpu", {}).get("count") is not None:
                _cs["threads"] = _cs.get("threads") or resp["cpu"]["count"]
            resp["cpu_summary"] = _cs
            resp["app_edition"] = _resolve_app_edition()
            return resp
        resp["device_type"] = None
        try:
            chassis_path = Path("/sys/class/dmi/id/chassis_type")
            if chassis_path.exists():
                try:
                    ct = chassis_path.read_text().strip()
                    if ct == "3":
                        resp["device_type"] = "desktop"
                    elif ct in ("8", "9", "10", "14"):
                        resp["device_type"] = "laptop"
                except Exception:
                    pass
        except Exception:
            pass
        pi_disc = discover_raspberry_pi_info()
        resp["is_raspberry_pi"] = pi_disc.get("is_raspberry_pi", False)
        resp["hardware"] = dict(pi_disc.get("hardware") or {"cpus": [], "gpus": []})
        pci_disc = discover_pci_info()
        if not resp.get("is_raspberry_pi"):
            resp["hardware"]["gpus"] = pci_disc.get("gpus") or []
        cpu_name = cpu_probe.get("name")
        if cpu_name:
            resp["cpu_name"] = cpu_name
        cpu_summary = dict(cpu_probe.get("summary") or {})
        cpu_summary["name"] = cpu_summary.get("name") or cpu_name
        # CPU-Kerne: Priorität: cpu_summary["cores"] > physical_cores > Fallback auf threads/2
        if resp.get("cpu", {}).get("physical_cores") is not None and resp["cpu"]["physical_cores"] > 0:
            cpu_summary["cores"] = cpu_summary.get("cores") or resp["cpu"]["physical_cores"]
        elif not cpu_summary.get("cores") and resp.get("cpu", {}).get("count"):
            # Fallback: Wenn keine Kerne gefunden, nimm threads/2 (typisch für Hyperthreading)
            cpu_summary["cores"] = max(1, resp["cpu"]["count"] // 2)
        if resp.get("cpu", {}).get("count") is not None:
            cpu_summary["threads"] = cpu_summary["threads"] or resp["cpu"]["count"]
        resp["cpu_summary"] = cpu_summary
        # Ein CPU-Eintrag für Anzeige (keine Liste aller Threads)
        if not resp.get("hardware", {}).get("cpus") and cpu_name:
            resp["hardware"]["cpus"] = [{"model": cpu_name, "processor_id": 0}]
        elif resp.get("hardware", {}).get("cpus") and len(resp["hardware"]["cpus"]) > 1:
            first_model = (resp["hardware"]["cpus"][0].get("model") or cpu_name or "CPU")
            resp["hardware"]["cpus"] = [{"model": first_model, "processor_id": 0}]
        resp["motherboard"] = discover_mainboard_info()
        resp["ram_info"] = discover_memory_info().get("ram_info") or []
        # Hersteller-Treiber-TIP: Was bieten NVIDIA/AMD/Intel-Treiber mehr als integrierte?
        gpu_names = " ".join([(g.get("name") or g.get("display_name") or "") for g in resp.get("hardware", {}).get("gpus", [])]).lower()
        cpu_name_lower = (resp.get("cpu_name") or "").lower()
        tips = []
        if "nvidia" in gpu_names:
            tips.append("NVIDIA: Hersteller-Treiber bieten bessere Raytracing-, CUDA- und AI-Unterstützung; bei neueren GPUs oft Open-Source-Kernel + proprietäre Userspace-Komponenten.")
        if "amd" in gpu_names or "radeon" in gpu_names:
            tips.append("AMD: Unter Linux meist Open-Source (Mesa/amdgpu) ausreichend; Hersteller-Seite für Profi-Software und neueste Features.")
        if "intel" in gpu_names or ("intel" in cpu_name_lower and not tips):
            tips.append("Intel: Mesa-Treiber oft ausreichend; Hersteller für neueste Medien-/Encode-Features.")
        resp["manufacturer_driver_tip"] = " ".join(tips) if tips else None
        # Alle Sensoren, Laufwerke, Lüfter, Displays (nach Neustart vollständig sichtbar)
        sensor_disc = discover_sensor_info()
        try:
            resp["sensors"] = sensor_disc.get("sensors") or []
            resp["disks"] = sensor_disc.get("disks") or []
            resp["fans"] = sensor_disc.get("fans") or []
            resp["displays"] = sensor_disc.get("displays") or []
        except Exception:
            resp["sensors"] = []
            resp["disks"] = []
            resp["fans"] = []
            resp["displays"] = []
        try:
            pci_list = pci_disc.get("pci_list") or []
            clean_gpu = pci_disc.get("clean_gpu_description")
            def _device_display(description: str) -> str:
                if not description:
                    return description or ""
                d = (description or "").lower()
                # Nur bei Grafik-Controller kurze Handelsbezeichnung; NVIDIA-Audio nicht bereinigen
                is_gpu = "vga" in d or "3d" in d or ("display" in d and ("nvidia" in d or "amd" in d or "intel" in d or "radeon" in d))
                if is_gpu and not ("nvidia" in d and "audio" in d) and callable(clean_gpu):
                    return clean_gpu(description)
                return description
            resp["drivers"] = [{"device": _device_display(p.get("description") or ""), "driver": p.get("driver") or "—"} for p in pci_list]
        except Exception:
            resp["drivers"] = []
        resp["network"] = build_network_section(use_demo=use_demo)
        if use_demo:
            resp["is_raspberry_pi"] = True  # Für Screenshots: Pi-spezifische Seiten anzeigen
        resp["app_edition"] = _resolve_app_edition()
        return resp
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def build_system_info_sections(*, light: bool = False, use_demo: bool = False) -> dict[str, Any]:
    """System info sections with facade vocabulary (read-only)."""
    warnings: list[SystemInfoFacadeWarning] = []
    errors: list[str] = []

    def _runtime() -> SystemInfoSection:
        data = build_runtime_section(light=light)
        mem_pct = float((data.get("memory") or {}).get("percent") or 0)
        cpu_pct = float((data.get("cpu") or {}).get("usage") or 0)
        if mem_pct >= 90 or cpu_pct >= 95:
            status = "warning"
        elif mem_pct > 0 or cpu_pct > 0:
            status = "ok"
        else:
            status = "unknown"
        return SystemInfoSection(
            section_id="runtime",
            status=build_section_status(status),
            data=data,
        )

    def _hardware() -> SystemInfoSection:
        if light:
            return SystemInfoSection(section_id="hardware", status="unknown", data={})
        data = build_hardware_section(use_demo=use_demo)
        return SystemInfoSection(
            section_id="hardware",
            status=build_section_status("ok" if data.get("hardware") else "unknown"),
            data=data,
        )

    def _network() -> SystemInfoSection:
        net = build_network_section(use_demo=use_demo)
        ips = net.get("ips") if isinstance(net.get("ips"), list) else []
        status = "ok" if ips else "warning"
        return SystemInfoSection(
            section_id="network",
            status=build_section_status(status),
            data={"network": net},
        )

    sections = [
        _safe_section("runtime", _runtime, facade_warnings=warnings, facade_errors=errors),
        _safe_section("hardware", _hardware, facade_warnings=warnings, facade_errors=errors),
        _safe_section("network", _network, facade_warnings=warnings, facade_errors=errors),
    ]
    return {
        "facade_version": SYSTEM_INFO_FACADE_VERSION,
        "sections": [asdict(s) for s in sections],
        "warnings": [asdict(w) for w in warnings],
        "errors": errors,
    }


def build_system_info_diagnostics() -> dict[str, Any]:
    """Lightweight facade diagnostics — no active probe."""
    return {
        "facade_version": SYSTEM_INFO_FACADE_VERSION,
        "facade_module": "core.system_info_facade",
        "status_vocabulary": sorted(FACADE_STATUS_VALUES),
        "delegates_to": [
            "network_info_facade.build_network_info",
            "network_info_facade.build_demo_network_info",
            "hardware_discovery.discover_cpu_info",
            "hardware_discovery.discover_memory_info",
            "hardware_discovery.discover_mainboard_info",
            "hardware_discovery.discover_pci_info",
            "hardware_discovery.discover_sensor_info",
            "hardware_discovery.discover_raspberry_pi_info",
            "hardware_discovery.run_command",
        ],
        "hardware_via_hardware_discovery": True,
        "public_functions": [
            "build_system_info",
            "build_system_info_sections",
            "build_hardware_section",
            "build_runtime_section",
            "build_network_section",
            "build_system_info_diagnostics",
        ],
        "routes_migrated_to_facade": [
            "GET /api/system-info",
        ],
        "network_via_network_info_facade": True,
        "read_only": True,
        "writes_allowed": False,
    }
