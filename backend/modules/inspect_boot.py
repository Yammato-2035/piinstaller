"""
Read-only Prüfungen zur Bootfähigkeit (laufendes Root oder angepasster Pfad).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run_capture(
    argv: list[str],
    *,
    runner: Runner | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def _find_efi_mount(*, runner: Runner | None = None) -> dict[str, Any]:
    r = _run_capture(["findmnt", "-J", "/boot/efi"], runner=runner, timeout=15)
    if r.returncode != 0 or not (r.stdout or "").strip():
        return {"present": False, "source": None, "fstype": None}
    try:
        import json

        data = json.loads(r.stdout or "{}")
    except Exception:
        return {"present": False, "source": None, "fstype": None}
    fss = data.get("filesystems")
    if not isinstance(fss, list) or not fss:
        return {"present": False, "source": None, "fstype": None}
    fs0 = fss[0]
    if not isinstance(fs0, dict):
        return {"present": False, "source": None, "fstype": None}
    return {
        "present": True,
        "source": fs0.get("source"),
        "fstype": fs0.get("fstype"),
        "target": fs0.get("target"),
    }


def analyze_boot_status(root: str | Path = "/", *, runner: Runner | None = None) -> dict[str, Any]:
    """
    Prüft typische Boot-Artefakte unter ``root`` (keine Modifikation).

    - ``/boot`` bzw. ``/boot/firmware`` (Pi)
    - Kernel- und initramfs-Dateien
    - ``/etc/fstab`` syntaktisch grob prüfen
    - optional ESP: ``findmnt /boot/efi``
    """
    base = Path(root)
    boot_dir = base / "boot"
    firmware_dir = boot_dir / "firmware"
    primary_boot = firmware_dir if firmware_dir.is_dir() else boot_dir

    status: dict[str, Any] = {
        "boot_dir_exists": boot_dir.is_dir(),
        "firmware_dir_used": firmware_dir.is_dir(),
        "primary_boot": str(primary_boot),
        "kernel_files": [],
        "initrd_files": [],
        "fstab_exists": False,
        "fstab_lines": 0,
        "fstab_parse_ok": True,
        "fstab_code": "rescue.boot.fstab_ok",
        "esp": _find_efi_mount(runner=runner),
        "codes": [],
    }

    if not boot_dir.is_dir():
        status["codes"].append("rescue.boot.boot_dir_missing")

    if primary_boot.is_dir():
        try:
            names = sorted(os.listdir(primary_boot))
        except OSError:
            names = []
        status["kernel_files"] = [n for n in names if n.startswith("vmlinuz") or n.startswith("Image")]
        status["initrd_files"] = [
            n for n in names if n.startswith("initrd") or n.startswith("initramfs") or n.startswith("initrd.img")
        ]

    fstab = base / "etc" / "fstab"
    status["fstab_exists"] = fstab.is_file()
    if not status["fstab_exists"]:
        status["fstab_code"] = "rescue.boot.fstab_missing"
        status["fstab_parse_ok"] = False
        status["codes"].append("rescue.boot.fstab_missing")
    else:
        try:
            text = fstab.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            status["fstab_parse_ok"] = False
            status["fstab_code"] = "rescue.boot.fstab_unreadable"
            status["codes"].append("rescue.boot.fstab_unreadable")
            status["fstab_error"] = str(e)
        else:
            lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
            status["fstab_lines"] = len(lines)
            for ln in lines:
                parts = ln.split()
                if len(parts) < 4:
                    status["fstab_parse_ok"] = False
                    status["fstab_code"] = "rescue.boot.fstab_parse_error"
                    status["codes"].append("rescue.boot.fstab_parse_error")
                    break

    if not status["kernel_files"]:
        status["codes"].append("rescue.boot.kernel_missing")
    if not status["initrd_files"]:
        status["codes"].append("rescue.boot.initrd_missing")

    if not status["codes"]:
        status["codes"].append("rescue.boot.layout_ok")

    return status


__all__ = ["analyze_boot_status"]
