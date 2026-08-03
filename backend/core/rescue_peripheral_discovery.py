"""
Rescue peripheral discovery — read-only USB/audio/input device inventory for
the rescue stick's system assessment. Same contract as
core.rescue_system_assessment_v2: read-only on target, missing tools ->
missing_tool, never crash.

Classification is keyword/heuristic-based (same approach already used by
backend/app.py::peripherals_scan() for the main product) rather than a full
USB device-class parser — good enough to point at a driver_catalog entry,
not a claim of exhaustive device identification.
"""

from __future__ import annotations

import subprocess
from typing import Any

_KEYBOARD_HINTS = ("keyboard", "tastatur")
_MOUSE_HINTS = ("mouse", "maus", "pointer")
_WEBCAM_HINTS = ("webcam", "camera", "kamera", "video", "uvc", "integrated camera")
_AUDIO_HINTS = ("audio", "headset", "microphone", "sound", "headphone")
_PRINTER_HINTS = ("printer", "drucker", "laserjet", "deskjet", "officejet", "mfp", "scanner")
_STORAGE_HINTS = ("mass storage", "flash drive", "external hdd", "external ssd", "card reader")
_AI_ACCELERATOR_HINTS = ("coral", "neural", "npu", "movidius", "edge tpu", "tpu")


def _run(cmd: list[str], *, timeout: int = 10) -> tuple[str, bool]:
  try:
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=timeout)
    return out, True
  except FileNotFoundError:
    return "", False
  except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
    return f"[error:{type(exc).__name__}]", True


def _classify_usb_line(desc: str) -> str:
  lowered = desc.lower()
  if any(h in lowered for h in _AI_ACCELERATOR_HINTS):
    return "ai_accelerator"
  if any(h in lowered for h in _PRINTER_HINTS):
    return "printer"
  if any(h in lowered for h in _KEYBOARD_HINTS):
    return "keyboard"
  if any(h in lowered for h in _MOUSE_HINTS):
    return "mouse"
  if any(h in lowered for h in _WEBCAM_HINTS):
    return "webcam"
  if any(h in lowered for h in _STORAGE_HINTS):
    return "storage"
  if any(h in lowered for h in _AUDIO_HINTS):
    return "audio"
  return "usb"


def _collect_usb_devices() -> dict[str, Any]:
  out, ok = _run(["lsusb"])
  devices: list[dict[str, str]] = []
  if ok:
    for line in out.splitlines():
      line = line.strip()
      if not line:
        continue
      devices.append({"description": line, "kind": _classify_usb_line(line)})
  return {
    "devices": devices,
    "missing_tools": [] if ok else ["lsusb"],
  }


def _collect_input_devices() -> dict[str, Any]:
  devices: list[dict[str, str]] = []
  missing: list[str] = []
  try:
    with open("/proc/bus/input/devices", encoding="utf-8", errors="replace") as fh:
      content = fh.read()
  except OSError:
    missing.append("/proc/bus/input/devices")
    content = ""
  for block in content.split("\n\n"):
    if not block.strip():
      continue
    name = ""
    handlers = ""
    for line in block.splitlines():
      if line.startswith("N: Name="):
        name = line.replace("N: Name=", "").strip().strip('"')
      elif line.startswith("H: Handlers="):
        handlers = line.replace("H: Handlers=", "").strip()
    if name and ("kbd" in handlers or "mouse" in handlers or "event" in handlers):
      devices.append({"name": name, "handlers": handlers})
  return {
    "devices": devices,
    "missing_tools": missing,
  }


def _collect_audio_devices() -> dict[str, Any]:
  out, ok = _run(["aplay", "-l"])
  cards: list[str] = []
  if ok:
    for line in out.splitlines():
      if line.startswith("card "):
        cards.append(line.strip())
  return {
    "cards": cards,
    "missing_tools": [] if ok else ["aplay"],
  }


def build_peripheral_inventory() -> dict[str, Any]:
  usb = _collect_usb_devices()
  input_devices = _collect_input_devices()
  audio = _collect_audio_devices()
  missing_tools = sorted(set(usb["missing_tools"]) | set(input_devices["missing_tools"]) | set(audio["missing_tools"]))
  return {
    "usb": usb,
    "input_devices": input_devices,
    "audio": audio,
    "missing_tools": missing_tools,
  }
