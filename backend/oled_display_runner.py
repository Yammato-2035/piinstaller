#!/usr/bin/env python3
"""
PI-Installer OLED Display Runner
Zeigt zyklisch ausgewählte Metriken auf SSD1306 OLED (I2C 0x3C/0x3D).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil


RUNNING = True


def _on_signal(_signum, _frame):
    global RUNNING
    RUNNING = False


def _is_pid_alive(pid: int) -> bool:
    try:
        if pid <= 1:
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def load_settings(path: Path) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "enabled": False,
        "metrics": {
            "temperature": {"enabled": True, "duration_seconds": 5},
            "utilization": {"enabled": True, "duration_seconds": 5},
            "memory_usage": {"enabled": True, "duration_seconds": 5},
            "ip_address": {"enabled": True, "duration_seconds": 5},
        },
    }
    try:
        if not path.exists():
            return defaults
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return defaults
        metrics = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}
        out = {
            "enabled": bool(raw.get("enabled", defaults["enabled"])),
            "metrics": {},
        }
        for key, default in defaults["metrics"].items():
            val = metrics.get(key, default)
            if isinstance(val, dict):
                enabled = bool(val.get("enabled", default["enabled"]))
                try:
                    dur = int(val.get("duration_seconds", default["duration_seconds"]))
                except Exception:
                    dur = default["duration_seconds"]
            else:
                enabled = bool(val)
                dur = default["duration_seconds"]
            out["metrics"][key] = {"enabled": enabled, "duration_seconds": max(1, min(120, dur))}
        return out
    except Exception:
        return defaults


def get_cpu_temp() -> str:
    try:
        value = Path("/sys/class/thermal/thermal_zone0/temp").read_text(encoding="utf-8").strip()
        return f"{int(value)/1000.0:.1f} C"
    except Exception:
        return "n/a"


def get_utilization() -> str:
    try:
        return f"{psutil.cpu_percent(interval=0.2):.0f}%"
    except Exception:
        return "n/a"


def get_memory_usage() -> str:
    try:
        return f"{psutil.virtual_memory().percent:.0f}%"
    except Exception:
        return "n/a"


def get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "n/a"


def _safe_percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def metric_info(metric: str) -> Tuple[str, str, int]:
    if metric == "temperature":
        temp_text = get_cpu_temp()
        try:
            temp_c = float(temp_text.split()[0])
            # 20..90 C -> 0..100%
            pct = _safe_percent(((temp_c - 20.0) / 70.0) * 100.0)
        except Exception:
            pct = 0
        return ("Temperatur", temp_text, pct)
    if metric == "utilization":
        txt = get_utilization()
        try:
            pct = _safe_percent(float(txt.replace("%", "").strip()))
        except Exception:
            pct = 0
        return ("Auslastung", txt, pct)
    if metric == "memory_usage":
        txt = get_memory_usage()
        try:
            pct = _safe_percent(float(txt.replace("%", "").strip()))
        except Exception:
            pct = 0
        return ("Speicher", txt, pct)
    return ("PI-Installer", "n/a", 0)


def draw_metric_page(draw, width: int, height: int, font, ip_text: str, metric: str) -> None:
    label, value_text, percent = metric_info(metric)
    # Kopfzeile mit IP (immer sichtbar)
    draw.rectangle((0, 0, width, 12), outline=255, fill=0)
    draw.text((2, 2), f"IP {ip_text}", font=font, fill=255)

    # Grafikbereich darunter (Tortendiagramm)
    pie_left = 4
    pie_top = 16
    pie_size = min(height - pie_top - 2, 44)
    pie_box = (pie_left, pie_top, pie_left + pie_size, pie_top + pie_size)
    draw.ellipse(pie_box, outline=255, fill=0)
    if percent > 0:
        end_angle = -90 + int(360 * (percent / 100.0))
        draw.pieslice(pie_box, start=-90, end=end_angle, outline=255, fill=255)
        # Loch in der Mitte für besseren "Donut"-Look auf Monochrom
        inset = 10
        inner = (
            pie_box[0] + inset,
            pie_box[1] + inset,
            pie_box[2] - inset,
            pie_box[3] - inset,
        )
        if inner[2] > inner[0] and inner[3] > inner[1]:
            draw.ellipse(inner, outline=255, fill=0)

    # Text rechts vom Diagramm
    text_x = pie_left + pie_size + 6
    draw.text((text_x, 20), label, font=font, fill=255)
    draw.text((text_x, 34), value_text, font=font, fill=255)
    # Wenn der Wert bereits Prozent enthält (z. B. "47%"), nicht doppelt anzeigen.
    if "%" not in value_text:
        draw.text((text_x, 48), f"{percent:3d}%", font=font, fill=255)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Pfad zur display-telemetry.json")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        print(f"[oled-runner] Fehlende OLED-Abhängigkeiten: {e}", flush=True)
        return 2

    config_path = Path(args.config).expanduser()
    pid_file = config_path.with_suffix(".pid")
    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        existing = None
        if pid_file.exists():
            raw = (pid_file.read_text(encoding="utf-8") or "").strip()
            if raw.isdigit():
                existing = int(raw)
        if existing and existing != os.getpid() and _is_pid_alive(existing):
            print(f"[oled-runner] Bereits aktiv (PID {existing}), beende Doppelstart.", flush=True)
            return 0
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    def _discover_i2c_ports() -> List[int]:
        ports = []
        try:
            for dev in Path("/dev").glob("i2c-*"):
                name = dev.name
                if "-" not in name:
                    continue
                idx = name.split("-")[-1]
                if idx.isdigit():
                    ports.append(int(idx))
        except Exception:
            pass
        ports = sorted(set(ports))
        if 1 in ports:
            ports = [1] + [p for p in ports if p != 1]
        if not ports:
            ports = [1]
        return ports

    def _try_init_device():
        for port in _discover_i2c_ports():
            for addr in (0x3C, 0x3D):
                try:
                    serial = i2c(port=port, address=addr)
                    # 180 Grad drehen
                    dev = ssd1306(serial, rotate=2)
                    print(f"[oled-runner] OLED initialisiert auf I2C-Bus {port}, Adresse 0x{addr:02x}", flush=True)
                    return dev
                except Exception:
                    continue
        return None

    font = ImageFont.load_default()
    device = _try_init_device()

    while RUNNING:
        if device is None:
            print("[oled-runner] Kein OLED auf 0x3C/0x3D erreichbar. Neuer Versuch in 2s.", flush=True)
            time.sleep(2.0)
            device = _try_init_device()
            continue

        settings = load_settings(config_path)
        if not settings.get("enabled", False):
            time.sleep(1.0)
            continue

        enabled_metrics = []
        for key, cfg in settings.get("metrics", {}).items():
            if isinstance(cfg, dict) and cfg.get("enabled", False):
                enabled_metrics.append((key, int(cfg.get("duration_seconds", 5))))

        if not enabled_metrics:
            time.sleep(1.0)
            continue

        # IP wird immer in der Kopfzeile gezeigt; "ip_address" nicht als eigene Seite rotieren
        rotating_metrics = [(m, d) for m, d in enabled_metrics if m != "ip_address"]

        if not rotating_metrics:
            rotating_metrics = [("utilization", 3)]

        for metric, duration in rotating_metrics:
            if not RUNNING:
                break
            ip_text = get_ip()
            image = Image.new("1", (device.width, device.height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, device.width, device.height), outline=0, fill=0)
            draw_metric_page(draw, device.width, device.height, font, ip_text, metric)
            try:
                device.display(image)
            except Exception:
                print("[oled-runner] OLED-Verbindung verloren. Reinitialisiere...", flush=True)
                device = None
                break

            end_at = time.time() + max(1, min(120, duration))
            while RUNNING and time.time() < end_at:
                time.sleep(0.2)

    if device is not None:
        try:
            image = Image.new("1", (device.width, device.height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, device.width, device.height), outline=0, fill=0)
            device.display(image)
        except Exception:
            pass
    try:
        if pid_file.exists():
            raw = (pid_file.read_text(encoding="utf-8") or "").strip()
            if raw == str(os.getpid()):
                pid_file.unlink(missing_ok=True)
    except Exception:
        pass
    print("[oled-runner] Beendet.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

