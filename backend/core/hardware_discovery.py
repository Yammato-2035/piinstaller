"""
Hardware Discovery Core — canonical read-only hardware/system discovery.

Phase G.9: logic extracted from ``app.py``; no new hardware rules, no API changes.
"""

from __future__ import annotations

import os
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

import psutil

HARDWARE_DISCOVERY_VERSION = 1


def _shell_run(cmd: str, *, timeout: int = 10) -> dict[str, Any]:
    """Shell command runner (legacy ``app.run_command`` shape for non-sudo probes)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout", "stdout": "", "stderr": ""}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc), "stdout": "", "stderr": ""}


def run_command(cmd: str, *, timeout: int = 10) -> dict[str, Any]:
    """Read-only probe alias used by extracted legacy helpers."""
    return _shell_run(cmd, timeout=timeout)


_pi_config_module = None


def _get_pi_config_module():
    global _pi_config_module
    if _pi_config_module is None:
        from modules.raspberry_pi_config import RaspberryPiConfigModule

        _pi_config_module = RaspberryPiConfigModule()
    return _pi_config_module


# --- get_cpu_temp (from app.py L5233-L5271) ---
def get_cpu_temp():
    """CPU Temperatur auslesen"""
    try:
        # Versuche verschiedene Pfade
        temp_paths = [
            '/sys/class/thermal/thermal_0/temp',
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/devices/virtual/thermal/thermal_zone0/temp',
        ]
        
        for path in temp_paths:
            try:
                with open(path, 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return round(temp, 1)
            except:
                continue
        
        # Alternative: vcgencmd (Raspberry Pi)
        result = run_command("vcgencmd measure_temp 2>/dev/null")
        if result["success"] and result["stdout"]:
            temp_str = result["stdout"]
            if "temp=" in temp_str:
                temp = float(temp_str.split("temp=")[1].split("'")[0])
                return round(temp, 1)
        
        # Alternative: sensors (falls installiert)
        result = run_command("sensors 2>/dev/null | grep -i temp | head -1")
        if result["success"] and result["stdout"]:
            # Parse sensors output
            parts = result["stdout"].split()
            for part in parts:
                if "+" in part and "°C" in part:
                    temp = float(part.replace("+", "").replace("°C", ""))
                    return round(temp, 1)
        
        return None
    except:
        return None


# --- get_all_thermal_sensors (from app.py L5273-L5317) ---
def get_all_thermal_sensors():
    """Alle Temperatursensoren (thermal_zone*)"""
    sensors = []
    try:
        base = Path("/sys/class/thermal")
        if not base.exists():
            return sensors
        for zone in sorted(base.glob("thermal_zone*")):
            try:
                temp_path = zone / "temp"
                type_path = zone / "type"
                if temp_path.exists():
                    temp = int(temp_path.read_text().strip()) / 1000.0
                    name = type_path.read_text().strip() if type_path.exists() else zone.name
                    sensors.append({"name": name, "temperature": round(temp, 1), "zone": zone.name})
            except Exception:
                continue
        if not sensors and run_command("which vcgencmd 2>/dev/null")["success"]:
            vc = run_command("vcgencmd measure_temp 2>/dev/null")
            if vc.get("success") and "temp=" in (vc.get("stdout") or ""):
                t = float((vc["stdout"] or "").split("temp=")[1].split("'")[0])
                sensors.append({"name": "cpu", "temperature": round(t, 1), "zone": "vcgencmd"})
        # hwmon Temperatursensoren (Motherboard, GPU, NVMe etc.)
        hwmon_base = Path("/sys/class/hwmon")
        if hwmon_base.exists():
            for hw in sorted(hwmon_base.iterdir()):
                if not hw.is_dir() or not hw.name.startswith("hwmon"):
                    continue
                try:
                    name_path = hw / "name"
                    hw_name = name_path.read_text().strip() if name_path.exists() else hw.name
                    for temp_path in sorted(hw.glob("temp*_input")):
                        try:
                            val = int(temp_path.read_text().strip())
                            temp_c = round(val / 1000.0, 1)
                            label_path = hw / temp_path.name.replace("_input", "_label")
                            label = label_path.read_text().strip() if label_path.exists() else temp_path.stem.replace("_input", "")
                            sensors.append({"name": f"{hw_name} {label}", "temperature": temp_c, "zone": f"{hw.name}/{temp_path.name}"})
                        except Exception:
                            continue
                except Exception:
                    continue
    except Exception:
        pass
    return sensors


# --- get_all_fans (from app.py L5319-L5339) ---
def get_all_fans():
    """Alle Lüfter (hwmon fan*_input)"""
    fans = []
    try:
        base = Path("/sys/class/hwmon")
        if not base.exists():
            return fans
        for hw in sorted(base.iterdir()):
            if not hw.is_dir() or not hw.name.startswith("hwmon"):
                continue
            name_path = hw / "name"
            name = name_path.read_text().strip() if name_path.exists() else hw.name
            for fan in sorted(hw.glob("fan*_input")):
                try:
                    rpm = int(fan.read_text().strip())
                    fans.append({"name": f"{name} {fan.stem.replace('_input', '')}", "rpm": rpm})
                except Exception:
                    continue
    except Exception:
        pass
    return fans


# --- get_all_disks (from app.py L5341-L5406) ---
def get_all_disks():
    """Alle gemounteten Laufwerke + NVMe/Block-Geräte mit Nutzung bzw. Größe"""
    disks = []
    seen_devices = set()
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "percent": usage.percent,
                    "label": part.device.rstrip("/").split("/")[-1],
                })
                seen_devices.add(part.device)
            except Exception:
                continue
        # NVMe und weitere Block-Geräte (auch ungemountet)
        block_base = Path("/sys/block")
        if block_base.exists():
            for blk in sorted(block_base.iterdir()):
                if blk.name.startswith("loop") or blk.name.startswith("ram"):
                    continue
                dev = f"/dev/{blk.name}"
                if dev in seen_devices:
                    continue
                try:
                    size_path = blk / "size"
                    if not size_path.exists():
                        continue
                    sectors = int(size_path.read_text().strip())
                    size_gb = round(sectors * 512 / (1024**3), 1)
                    if size_gb <= 0:
                        continue
                    # Mountpoint und Nutzung für dieses Block-Device ermitteln (z. B. nvme0n1p1)
                    mountpoint = ""
                    used_gb = None
                    percent = None
                    for p in psutil.disk_partitions(all=True):
                        if p.device.startswith(dev) or (dev + "1" == p.device or dev + "p1" == p.device):
                            try:
                                u = psutil.disk_usage(p.mountpoint)
                                mountpoint = p.mountpoint
                                used_gb = round(u.used / (1024**3), 1)
                                percent = u.percent
                                break
                            except Exception:
                                pass
                    disks.append({
                        "device": dev,
                        "mountpoint": mountpoint,
                        "fstype": "",
                        "total_gb": size_gb,
                        "used_gb": used_gb,
                        "percent": percent,
                        "label": blk.name,
                    })
                    seen_devices.add(dev)
                except Exception:
                    continue
    except Exception:
        pass
    return disks


# --- get_all_displays (from app.py L5408-L5438) ---
def get_all_displays():
    """Alle erkannten Displays (xrandr)"""
    displays = []
    try:
        r = run_command("xrandr --query 2>/dev/null")
        if not r.get("success") or not r.get("stdout"):
            return displays
        current = None
        for line in (r["stdout"] or "").strip().split("\n"):
            if line.startswith(" ") and "x" in line and "+" in line:
                parts = line.strip().split()
                if len(parts) >= 1 and current:
                    mode = parts[0]
                    displays.append({"output": current, "mode": mode, "connected": "connected" in line or "*" in line})
            else:
                parts = line.split()
                if len(parts) >= 2:
                    current = parts[0]
                    if parts[1] == "connected":
                        displays.append({"output": current, "mode": parts[2] if len(parts) > 2 else "", "connected": True})
        if not displays:
            r2 = run_command("DISPLAY=:0 xrandr --query 2>/dev/null")
            if r2.get("success") and r2.get("stdout"):
                for line in (r2["stdout"] or "").strip().split("\n"):
                    if " connected " in line:
                        parts = line.split()
                        if len(parts) >= 1:
                            displays.append({"output": parts[0], "mode": parts[2] if len(parts) > 2 else "", "connected": True})
    except Exception:
        pass
    return displays


# --- get_fan_speed (from app.py L5440-L5446) ---
def get_fan_speed():
    """Lüfter-Geschwindigkeit (ein Wert für Abwärtskompatibilität)"""
    try:
        fans = get_all_fans()
        return fans[0]["rpm"] if fans else None
    except Exception:
        return None


# --- get_motherboard_info (from app.py L5565-L5586) ---
def get_motherboard_info():
    """Motherboard/Baseboard aus DMI"""
    info = {}
    try:
        for key, path in [("vendor", "board_vendor"), ("name", "board_name"), ("product", "product_name")]:
            p = Path("/sys/class/dmi/id") / path
            if p.exists():
                try:
                    info[key] = p.read_text().strip()
                except Exception:
                    pass
        if not info:
            r = run_command("dmidecode -t baseboard 2>/dev/null")
            if r.get("success") and r.get("stdout"):
                for line in (r["stdout"] or "").split("\n"):
                    if "Manufacturer:" in line:
                        info["vendor"] = line.split(":", 1)[-1].strip()
                    elif "Product Name:" in line:
                        info["name"] = line.split(":", 1)[-1].strip()
    except Exception:
        pass
    return info


# --- get_ram_info (from app.py L5588-L5616) ---
def get_ram_info():
    """RAM-Typ, Geschwindigkeit und Hersteller (DMI/dmidecode). Normalisierte Felder: Type, Size, Speed, Manufacturer."""
    rams = []
    try:
        r = run_command("dmidecode -t memory 2>/dev/null")
        if r.get("success") and r.get("stdout"):
            block = {}
            for line in (r["stdout"] or "").split("\n"):
                if line.startswith("Memory Device"):
                    if block.get("Size") and "No Module" not in (block.get("Size") or ""):
                        _normalize_ram_block(block)
                        rams.append(block)
                    block = {}
                elif ":" in line:
                    k, v = line.split(":", 1)
                    block[k.strip()] = v.strip()
            if block.get("Size") and "No Module" not in (block.get("Size") or ""):
                _normalize_ram_block(block)
                rams.append(block)
        if not rams:
            for p in Path("/sys/class/dmi/id").glob("*"):
                if "mem" in p.name.lower():
                    try:
                        rams.append({"source": p.name, "value": p.read_text().strip()})
                    except Exception:
                        pass
    except Exception:
        pass
    return rams


# --- _normalize_ram_block (from app.py L5619-L5625) ---
def _normalize_ram_block(block: dict) -> None:
    """Setzt Speed aus dmidecode (Fallback: Configured Clock Speed / Maximum Speed). Type, Size, Manufacturer bleiben unverändert."""
    if not block:
        return
    speed = block.get("Speed") or block.get("Configured Clock Speed") or block.get("Configured Memory Speed") or block.get("Maximum Speed")
    if speed and str(speed).strip() and str(speed) != "Unknown":
        block["Speed"] = speed


# --- get_cpu_name (from app.py L5627-L5659) ---
def get_cpu_name():
    """CPU- oder Board-Modellname aus /proc/cpuinfo oder Device-Tree (für Raspberry Pi 5/ARM64)."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                s = line.strip()
                if s.startswith("model name"):
                    return line.split(":", 1)[-1].strip()
                if s.startswith("Model name"):
                    return line.split(":", 1)[-1].strip()
                if s.startswith("Hardware"):
                    return line.split(":", 1)[-1].strip()
                if s.startswith("Model") and ":" in line:
                    # "Model" (Board, z. B. "Raspberry Pi 5 Model B Rev 1.0") – nur wenn noch nichts gefunden
                    val = line.split(":", 1)[-1].strip()
                    if val and ("Raspberry" in val or "BCM" in val):
                        return val
                if s.startswith("Processor"):
                    val = line.split(":", 1)[-1].strip()
                    if val and "aarch64" in val.lower():
                        return val
        # Fallback: Device-Tree (Raspberry Pi Board-Name)
        for path in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
            try:
                if Path(path).exists():
                    raw = Path(path).read_bytes().decode("utf-8", errors="ignore").rstrip("\x00").strip()
                    if raw:
                        return raw
            except Exception:
                pass
        return None
    except Exception:
        return None


# --- get_cpu_summary (from app.py L5662-L5724) ---
def get_cpu_summary():
    """Ein CPU-Summary: Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (flags) aus /proc/cpuinfo und lscpu."""
    out = {"name": None, "cores": None, "threads": None, "cache": None, "flags": None}
    try:
        # Aus /proc/cpuinfo (erstes Prozessor-Block)
        with open("/proc/cpuinfo", "r") as f:
            content = f.read()
        blocks = content.strip().split("\n\n")
        first = blocks[0] if blocks else ""
        for line in first.split("\n"):
            line = line.strip()
            if line.startswith("model name") or line.startswith("Model name"):
                out["name"] = line.split(":", 1)[-1].strip()
            elif line.startswith("Hardware") and not out["name"]:
                out["name"] = line.split(":", 1)[-1].strip()
            elif line.startswith("Model") and ":" in line and not out["name"]:
                val = line.split(":", 1)[-1].strip()
                if val and ("Raspberry" in val or "BCM" in val):
                    out["name"] = val
            elif line.startswith("Processor") and not out["name"]:
                out["name"] = line.split(":", 1)[-1].strip()
            elif line.startswith("cpu cores"):
                try:
                    out["cores"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("cache size"):
                out["cache"] = line.split(":", 1)[-1].strip()
            elif line.startswith("flags") or line.startswith("Features"):
                out["flags"] = line.split(":", 1)[-1].strip()
        # Threads = Anzahl Prozessor-Blöcke
        out["threads"] = len([b for b in blocks if "processor" in b or "Processor" in b])
        # lscpu für Kerne (Core(s) per socket × Sockets) sowie L1d/L1i/L2/L3
        try:
            r = run_command("lscpu 2>/dev/null")
            if r.get("success") and r.get("stdout"):
                cores_per_socket = None
                sockets = None
                for line in (r.get("stdout") or "").splitlines():
                    if "Core(s) per socket:" in line:
                        try:
                            cores_per_socket = int(line.split(":")[-1].strip())
                        except ValueError:
                            pass
                    elif "Socket(s):" in line:
                        try:
                            sockets = int(line.split(":")[-1].strip())
                        except ValueError:
                            pass
                    elif "L1d cache:" in line or "L1i cache:" in line or "L2 cache:" in line or "L3 cache:" in line:
                        key, _, val = line.partition(":")
                        val = val.strip()
                        if val:
                            out["cache"] = (out["cache"] or "") + (" · " if out["cache"] else "") + f"{key.strip()}: {val}"
                if out.get("cores") is None and cores_per_socket is not None and sockets is not None:
                    out["cores"] = cores_per_socket * sockets
        except Exception:
            pass
        if out["cache"]:
            out["cache"] = out["cache"].strip()
        return out
    except Exception:
        return out


# --- get_per_core_usage (from app.py L5727-L5759) ---
def get_per_core_usage(per_cpu_percent):
    """Aus per-logical-CPU-Auslastung die pro physikalischem Kern (max der Threads) berechnen."""
    if not per_cpu_percent:
        return [], 0
    try:
        proc_to_core = {}
        with open("/proc/cpuinfo", "r") as f:
            proc_id = None
            core_id = None
            for line in f:
                if line.strip().startswith("processor"):
                    proc_id = int(line.split(":")[-1].strip())
                elif line.strip().startswith("core id"):
                    core_id = int(line.split(":")[-1].strip())
                elif line.strip() == "" and proc_id is not None and core_id is not None:
                    proc_to_core[proc_id] = core_id
                    proc_id = core_id = None
            if proc_id is not None and core_id is not None:
                proc_to_core[proc_id] = core_id
        from collections import defaultdict
        core_to_procs = defaultdict(list)
        for p, c in proc_to_core.items():
            core_to_procs[c].append(p)
        if not core_to_procs:
            return list(per_cpu_percent), len(per_cpu_percent)
        per_core = []
        for c in sorted(core_to_procs.keys()):
            procs = core_to_procs[c]
            vals = [per_cpu_percent[i] for i in procs if i < len(per_cpu_percent)]
            per_core.append(max(vals) if vals else 0)
        return per_core, len(per_core)
    except Exception:
        return list(per_cpu_percent), len(per_cpu_percent)


# --- _AMD_IGPU_CODENAMES (from app.py L9729-L9738) ---
_AMD_IGPU_CODENAMES = {
    "raphael": "AMD Radeon 610M (integriert)",   # Ryzen 7045/7945
    "phoenix": "AMD Radeon 760M (integriert)",   # Ryzen 7040
    "phoenix2": "AMD Radeon 760M (integriert)",
    "renoir": "AMD Radeon Graphics (integriert)",  # Ryzen 4000
    "cezanne": "AMD Radeon Graphics (integriert)",  # Ryzen 5000
    "vangogh": "AMD Radeon Graphics (integriert)",
    "rembrandt": "AMD Radeon 680M (integriert)",
    "stoney": "AMD Radeon R5/R7 (integriert)",
}


# --- _clean_gpu_description (from app.py L9741-L9825) ---
def _clean_gpu_description(desc: str) -> str:
    """Entfernt technische Bezeichnungen (VGA compatible controller, Audio device, rev xx) und liefert kurze Handelsbezeichnung."""
    if not (desc or "").strip():
        return desc or ""
    s = desc.strip()
    low = s.lower()
    # Audio-Geräte sind keine Grafik – leeren String zurück (wird vom Aufrufer gefiltert)
    if "audio device" in low or (low.startswith("audio ") and "nvidia" in low):
        return ""
    # Führende Controller-Typen entfernen (VGA compatible controller, 3D, Display controller – Benutzer braucht sie nicht)
    if low.startswith("vga ") or low.startswith("vga compatible") or "vga compatible controller:" in low:
        colon = s.find(":")
        if colon >= 0:
            s = s[colon + 1 :].strip()
            low = s.lower()
        else:
            for prefix in ("VGA compatible controller ", "VGA compatible controller: ", "vga compatible controller "):
                if low.startswith(prefix) or prefix.lower() in low:
                    start = low.find("vga compatible controller")
                    end = start + len("vga compatible controller")
                    if end < len(s) and s[end : end + 1] in (":", " "):
                        s = s[end + 1 :].lstrip(": ").strip()
                    low = s.lower()
                    break
    else:
        for prefix in ["3d ", "display controller: ", "display controller:"]:
            if low.startswith(prefix):
                s = s[len(prefix):].strip()
                low = s.lower()
                break
    # "(rev xx)" am Ende entfernen
    if " (rev " in s and ")" in s:
        idx = s.find(" (rev ")
        if idx > 0:
            s = s[:idx].strip()
    # NVIDIA: Nur Inhalt der eckigen Klammer als Handelsname (z. B. [GeForce RTX 4070 Max-Q / Mobile])
    if "nvidia" in s.lower() and "[" in s and "]" in s:
        start = s.find("[")
        end = s.find("]", start)
        if start >= 0 and end > start:
            name = s[start + 1 : end].strip()
            if name.lower().startswith("geforce") or name.lower().startswith("quadro") or "rtx" in name.lower():
                return "NVIDIA " + name
            return "NVIDIA " + name
    # AMD/ATI: Codenamen (Raphael, Phoenix) -> lesbare Bezeichnung aus Herstellerdaten
    if "amd" in s.lower() or "ati" in s.lower():
        s_lower = s.lower()
        for codename, label in _AMD_IGPU_CODENAMES.items():
            if codename in s_lower:
                return label
        for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI] ", "AMD/ATI ", "AMD "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        # Letzte eckige Klammer oft Codename (z. B. [AMD/ATI] Raphael)
        if "[" in s and "]" in s:
            bracket = s[s.rfind("[") + 1 : s.rfind("]")].strip()
            codename = bracket.split()[-1].lower() if bracket else ""
            if codename in _AMD_IGPU_CODENAMES:
                return _AMD_IGPU_CODENAMES[codename]
            if bracket and bracket.lower() not in ("amd/ati", "amd"):
                return "AMD " + bracket
        if s and not s.lower().startswith("vga"):
            return s
    # Sicherheit: verbliebene technische Präfixe am Anfang entfernen
    low = s.strip().lower()
    for strip_prefix in ("vga compatible controller:", "vga compatible controller", "audio device:"):
        if low.startswith(strip_prefix):
            s = s[len(strip_prefix):].lstrip(" ").strip()
            low = s.lower()
            break
    # Intel: Nur Grafik-Bezeichnung (UHD Graphics 770, Iris Xe etc.), ohne Chip-Code
    if "intel" in s.lower():
        low = s.lower()
        for marker in ["uhd graphics", "iris xe", "iris graphics", "hd graphics", "iris plus"]:
            i = low.find(marker)
            if i >= 0:
                part = s[i:].strip()
                return "Intel " + part
        for prefix in ["Intel Corporation ", "Intel "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        return "Intel " + s if s else s
    return s.strip()


# --- _shorten_gpu_display_name (from app.py L9828-L9885) ---
def _shorten_gpu_display_name(name: str, gpu_type: str, memory_mb: Optional[int] = None) -> tuple:
    """Liefert (display_name, memory_display). Handelsbezeichnung kurz, Speicher in GB (ggf. GDDR)."""
    name = (name or "").strip()
    n = name.lower()
    mem_display = ""
    if memory_mb is not None and memory_mb > 0:
        gb = memory_mb / 1024
        if gb >= 1:
            mem_display = f"{int(round(gb))} GB"
            if "nvidia" in n and ("rtx 40" in n or "rtx 30" in n or "geforce rtx" in n):
                mem_display += " GDDR6"
            elif "nvidia" in n:
                mem_display += " GDDR5/GDDR6"
        else:
            mem_display = f"{memory_mb} MB"
    # NVIDIA: Bereits bereinigt (z. B. "NVIDIA GeForce RTX 4070 Max-Q / Mobile") oder aus nvidia-smi – nur Prefix prüfen
    if "nvidia" in n and ("geforce" in n or "quadro" in n or "rtx" in n):
        if "corporation" not in n and "vga compatible" not in n and " (rev " not in n and "[" not in name:
            return (name if name.strip().lower().startswith("nvidia") else "NVIDIA " + name.strip(), mem_display)
        s = name.replace("NVIDIA Corporation", "").strip()
        for skip in ["GPU", "Graphics", "NVIDIA "]:
            if s.startswith(skip):
                s = s[len(skip):].strip()
        if "Laptop" in name:
            s = s.replace(" Laptop GPU", "").replace(" Laptop", "").strip() + " Laptop"
        elif "Mobile" in name or "Max-Q" in name:
            s = s.replace(" Mobile", "").replace(" Max-Q", "").strip()
            if "Max-Q" in name:
                s += " Max-Q"
            elif "Mobile" in name:
                s += " Mobile"
        if not s.startswith("NVIDIA"):
            s = "NVIDIA " + s
        return (s.strip() or name, mem_display)
    # Intel: z. B. "Intel UHD Graphics 770" / "Intel Iris Xe Graphics"
    if "intel" in n:
        for marker in ["uhd graphics", "iris xe", "iris graphics", "hd graphics", "iris plus", "graphics"]:
            if marker in n:
                i = n.find(marker)
                part = name[i:].strip() if i >= 0 else name
                return ("Intel " + part, mem_display)
        return (name.split("]")[-1].strip() if "]" in name else name, mem_display)
    # AMD: integriert (Radeon 610M, 760M, Radeon Graphics) vs. diskret (RX 6800)
    if "amd" in n or "radeon" in n or "ati" in n:
        if "radeon graphics" in n or "vega" in n or "610m" in n or "760m" in n or ("radeon" in n and "rx " not in n and "graphics" in n):
            short = name
            for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI]", "AMD/ATI", "AMD"]:
                if short.startswith(prefix):
                    short = short[len(prefix):].strip()
            if gpu_type == "integrated" and "integriert" not in short.lower():
                short = short + " (integriert)" if short else "AMD Radeon (integriert)"
            return (short or name, mem_display)
        short = name.split("[")[-1].split("]")[0].strip() if "[" in name else name
        for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI]", "AMD/ATI", "AMD"]:
            if short.startswith(prefix):
                short = short[len(prefix):].strip()
        return (short or name, mem_display)
    return (name, mem_display)


# --- _get_gpus_for_system_info (from app.py L9888-L9958) ---
def _get_gpus_for_system_info():
    """GPU-Liste für System-Info (Nicht-Pi): Handelsbezeichnung kurz, Speicher in GB. iGPU getrennt, Audio-Geräte nie als Grafik."""
    gpus = []
    try:
        pci_list = _get_pci_with_drivers()
        seen = set()
        for item in pci_list:
            desc = (item.get("description") or "").strip()
            desc_lower = desc.lower()
            # Audio-Geräte sind keine Grafikkarten – immer ausblenden (NVIDIA HDMI-Audio, Audio device, etc.)
            if "audio device" in desc_lower or "high definition audio" in desc_lower or "hdmi audio" in desc_lower or ("audio" in desc_lower and "nvidia" in desc_lower):
                continue
            # Nur echte Grafik-Controller: VGA, 3D, Display – kein reines "NVIDIA" (könnte Audio sein)
            is_vga_3d_display = "vga" in desc_lower or "3d" in desc_lower or "display" in desc_lower
            is_intel_graphics = "intel" in desc_lower and ("graphics" in desc_lower or "uhd" in desc_lower or "iris" in desc_lower or "vga" in desc_lower)
            is_amd_radeon = ("radeon" in desc_lower or "amd" in desc_lower or "ati" in desc_lower) and ("graphics" in desc_lower or "vga" in desc_lower or "display" in desc_lower or "raphael" in desc_lower or "phoenix" in desc_lower)
            is_nvidia_graphics = "nvidia" in desc_lower and (is_vga_3d_display or "geforce" in desc_lower or "quadro" in desc_lower or "rtx" in desc_lower or "gtx" in desc_lower)
            if not (is_vga_3d_display or is_intel_graphics or is_amd_radeon or is_nvidia_graphics):
                continue
            # Typ: integriert (Intel iGPU, AMD Codenamen Raphael/Phoenix, Radeon Graphics) vs. diskret
            gpu_type = "discrete"
            if is_intel_graphics:
                gpu_type = "integrated"
            elif is_amd_radeon and (
                "radeon graphics" in desc_lower or "vega" in desc_lower or "610m" in desc_lower or "760m" in desc_lower
                or ("radeon" in desc_lower and "rx " not in desc_lower)
                or any(c in desc_lower for c in ("raphael", "phoenix", "renoir", "cezanne", "rembrandt", "vangogh", "stoney"))
            ):
                gpu_type = "integrated"
            # Kurze Handelsbezeichnung (ohne "VGA compatible controller", ohne "rev xx", NVIDIA = Inhalt [...], AMD = Codenamen-Map)
            clean_name = _clean_gpu_description(desc)
            if not clean_name or clean_name in seen:
                continue
            seen.add(clean_name)
            gpus.append({"name": clean_name, "memory_mb": None, "driver": item.get("driver"), "gpu_type": gpu_type})
        if not gpus:
            r = run_command("lspci 2>/dev/null | grep -iE 'vga|3d|display'")
            if r.get("success") and r.get("stdout"):
                for line in (r["stdout"] or "").strip().split("\n"):
                    line_lower = line.lower()
                    if line.strip() and "audio" not in line_lower and "audio device" not in line_lower:
                        raw = line.split(" ", 1)[1] if " " in line else line.strip()
                        clean_name = _clean_gpu_description(raw)
                        if clean_name and clean_name not in seen:
                            seen.add(clean_name)
                            gpus.append({"name": clean_name.strip(), "memory_mb": None, "gpu_type": "discrete"})
        # NVIDIA: Name + Speicher aus nvidia-smi (Handelsbezeichnung, Speicher in GB)
        nv = run_command("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null")
        if nv.get("success") and nv.get("stdout"):
            nvidia_in_gpus = [g for g in gpus if "nvidia" in (g.get("name") or "").lower()]
            for idx, line in enumerate((nv["stdout"] or "").strip().split("\n")):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and idx < len(nvidia_in_gpus):
                    try:
                        mem_mb = int(parts[1].strip().split()[0])
                        nvidia_in_gpus[idx]["memory_mb"] = mem_mb
                        nvidia_in_gpus[idx]["name"] = parts[0].strip()  # nvidia-smi Name (kürzer als lspci)
                    except (ValueError, IndexError):
                        pass
        # display_name + memory_display für jede GPU
        for g in gpus:
            display_name, memory_display = _shorten_gpu_display_name(
                g.get("name"), g.get("gpu_type", "discrete"), g.get("memory_mb")
            )
            g["display_name"] = display_name
            g["memory_display"] = memory_display
    except Exception:
        pass
    return gpus


# --- _get_pci_with_drivers (from app.py L9963-L9987) ---
def _get_pci_with_drivers():
    """lspci -k: PCI-Geräte mit Kernel-Treiber; gibt Liste (address, line, driver) zurück."""
    result = run_command("/usr/bin/lspci -k 2>/dev/null")
    if not result.get("success") or not result.get("stdout"):
        result = run_command("lspci -k 2>/dev/null")
    if not result.get("success") or not result.get("stdout"):
        return []
    lines = (result["stdout"] or "").strip().split("\n")
    out = []
    current_addr = ""
    current_line = ""
    current_driver = ""
    for line in lines:
        if line and not line.startswith("\t"):
            if current_addr and current_line:
                out.append({"address": current_addr, "description": current_line, "driver": current_driver or None})
            parts = line.split(None, 1)
            current_addr = parts[0] if parts else ""
            current_line = parts[1] if len(parts) > 1 else ""
            current_driver = ""
        elif line.strip().startswith("Kernel driver in use:"):
            current_driver = line.split(":", 1)[-1].strip()
    if current_addr and current_line:
        out.append({"address": current_addr, "description": current_line, "driver": current_driver or None})
    return out



def discover_cpu_info(*, per_cpu_percent: list[float] | None = None) -> dict[str, Any]:
    """CPU discovery bundle (legacy shapes preserved)."""
    per_core_usage: list[Any] = []
    physical_cores = 0
    if per_cpu_percent:
        per_core_usage, physical_cores = get_per_core_usage(per_cpu_percent)
    return {
        "name": get_cpu_name(),
        "summary": get_cpu_summary(),
        "temperature": get_cpu_temp(),
        "fan_speed": get_fan_speed(),
        "per_core_usage": per_core_usage,
        "physical_cores": physical_cores,
    }


def discover_memory_info() -> dict[str, Any]:
    """RAM discovery (legacy ``get_ram_info`` list)."""
    rams = get_ram_info()
    return {"ram_info": rams if isinstance(rams, list) else []}


def discover_mainboard_info() -> dict[str, Any]:
    """Motherboard/Baseboard discovery (legacy dict)."""
    info = get_motherboard_info()
    return info if isinstance(info, dict) else {}


def discover_pci_info() -> dict[str, Any]:
    """PCI + GPU discovery for system-info."""
    pci_list = _get_pci_with_drivers()
    gpus = _get_gpus_for_system_info()
    return {
        "pci_list": pci_list if isinstance(pci_list, list) else [],
        "gpus": gpus if isinstance(gpus, list) else [],
        "clean_gpu_description": _clean_gpu_description,
    }


def discover_sensor_info() -> dict[str, Any]:
    """Thermal sensors, disks, fans, displays."""
    return {
        "sensors": get_all_thermal_sensors(),
        "disks": get_all_disks(),
        "fans": get_all_fans(),
        "displays": get_all_displays(),
    }


def discover_raspberry_pi_info() -> dict[str, Any]:
    """Raspberry Pi module probe + hardware cpus/gpus."""
    hardware = {"cpus": [], "gpus": []}
    pi_raw: dict[str, Any] = {"status": "error"}
    is_raspberry_pi = False
    try:
        pi_mod = _get_pi_config_module()
        pi_raw = pi_mod.get_system_info()
        if isinstance(pi_raw, dict) and pi_raw.get("status") == "success" and pi_raw.get("system_info"):
            si = pi_raw["system_info"]
            hardware = {
                "cpus": si.get("cpus") or [],
                "gpus": si.get("gpus") or [],
            }
            cpu_model = (si.get("cpu_model") or "").lower()
            gpus = si.get("gpus") or []
            if "raspberry" in cpu_model or "bcm27" in cpu_model:
                is_raspberry_pi = True
            elif gpus and "videocore" in (gpus[0].get("name") or "").lower():
                is_raspberry_pi = True
    except Exception:
        pass
    if not is_raspberry_pi:
        for model_path in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
            try:
                if Path(model_path).exists():
                    model = Path(model_path).read_bytes().decode("utf-8", errors="ignore").rstrip("\x00").lower()
                    if "raspberry" in model:
                        is_raspberry_pi = True
                        break
            except Exception:
                pass
    return {
        "pi_system_info": pi_raw if isinstance(pi_raw, dict) else {"status": "error"},
        "hardware": hardware,
        "is_raspberry_pi": is_raspberry_pi,
    }


def build_hardware_discovery_diagnostics() -> dict[str, Any]:
    """Lightweight discovery diagnostics — read-only."""
    return {
        "discovery_version": HARDWARE_DISCOVERY_VERSION,
        "discovery_module": "core.hardware_discovery",
        "public_functions": [
            "discover_cpu_info",
            "discover_memory_info",
            "discover_mainboard_info",
            "discover_pci_info",
            "discover_sensor_info",
            "discover_raspberry_pi_info",
            "build_hardware_discovery_diagnostics",
        ],
        "delegates_from_app_wrappers": [
            "get_cpu_temp",
            "get_cpu_name",
            "get_cpu_summary",
            "get_per_core_usage",
            "get_fan_speed",
            "get_motherboard_info",
            "get_ram_info",
            "get_all_thermal_sensors",
            "get_all_disks",
            "get_all_fans",
            "get_all_displays",
            "_get_pci_with_drivers",
            "_get_gpus_for_system_info",
            "_clean_gpu_description",
            "_get_pi_config_module",
        ],
        "read_only": True,
        "writes_allowed": False,
        "no_app_import_in_facade": True,
    }
