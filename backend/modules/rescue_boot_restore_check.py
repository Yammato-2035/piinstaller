"""
Rescue Phase 2D: Bootfähigkeit nach simuliertem Restore bewerten (nur Lesen, keine BL-Schreibaktionen).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from modules.inspect_boot import analyze_boot_status
from modules.inspect_storage import detect_filesystems

Runner = Callable[..., Any] | None


def inspect_restored_boot_layout(root: str | Path, *, runner: Runner = None) -> dict[str, Any]:
    """Mappt auf ``analyze_boot_status`` für extrahiertes Wurzelverzeichnis."""
    return analyze_boot_status(root, runner=runner)


def validate_kernel_presence(boot_status: dict[str, Any]) -> dict[str, Any]:
    k = boot_status.get("kernel_files") or []
    return {"ok": bool(k), "count": len(k), "code": "rescue.bootability.kernel_ok" if k else "rescue.bootability.kernel_missing"}


def validate_initramfs_presence(boot_status: dict[str, Any]) -> dict[str, Any]:
    k = boot_status.get("initrd_files") or []
    return {"ok": bool(k), "count": len(k), "code": "rescue.bootability.initrd_ok" if k else "rescue.bootability.initrd_uncertain"}


def validate_fstab_mapping(root: str | Path, *, runner: Runner = None) -> dict[str, Any]:
    """
    Prüft, ob UUID=/dev/PARTUUID-Einträge in fstab in der aktuellen blkid-Map vorkommen.

    Hinweis: Nach Restore auf neuer Hardware können UUIDs abweichen — dann ``uncertain``.
    """
    base = Path(root)
    fstab = base / "etc" / "fstab"
    out: dict[str, Any] = {
        "ok": True,
        "code": "rescue.bootability.fstab_mapping_ok",
        "missing_uuids": [],
        "unresolved": [],
    }
    if not fstab.is_file():
        out["ok"] = False
        out["code"] = "rescue.bootability.fstab_missing"
        return out
    try:
        text = fstab.read_text(encoding="utf-8", errors="replace")
    except OSError:
        out["ok"] = False
        out["code"] = "rescue.bootability.fstab_unreadable"
        return out

    blk = detect_filesystems(runner=runner)
    uuid_set = {v.get("uuid") for v in blk.values() if v.get("uuid")}

    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        spec = parts[0]
        if spec.startswith("UUID="):
            u = spec.split("=", 1)[1]
            if u and u not in uuid_set:
                out["missing_uuids"].append(u)
        elif spec.startswith("PARTUUID="):
            out["unresolved"].append(spec)
        elif spec.startswith("/dev/"):
            out["unresolved"].append(spec)

    if out["missing_uuids"]:
        out["ok"] = False
        out["code"] = "rescue.bootability.fstab_uuid_not_found_live"
    elif out["unresolved"] and not out["missing_uuids"]:
        out["code"] = "rescue.bootability.fstab_device_refs_uncertain"

    return out


def validate_bootloader_requirements(boot_status: dict[str, Any], root: str | Path) -> dict[str, Any]:
    """
    Heuristik: ESP sinnvoll für x86-EFI; Pi: /boot/firmware genutzt.

    Keine grub-install-Prüfung — nur Datei-/Mount-Hinweise.
    """
    base = Path(root)
    out: dict[str, Any] = {"platform_hint": "unknown", "codes": []}
    fw = base / "boot" / "firmware"
    if fw.is_dir():
        out["platform_hint"] = "raspberry_pi_like"
        out["codes"].append("rescue.bootability.firmware_dir_present")
    esp = boot_status.get("esp") or {}
    if esp.get("present"):
        out["platform_hint"] = "efi_like"
        out["codes"].append("rescue.bootability.esp_present")
    if not esp.get("present") and not fw.is_dir():
        out["codes"].append("rescue.bootability.bootloader_context_uncertain")
    return out


def estimate_bootability(
    boot_status: dict[str, Any],
    fstab_map: dict[str, Any],
    bootloader: dict[str, Any],
) -> dict[str, Any]:
    """
    Ergebnis ``bootability_class``: BOOTABLE_LIKELY | BOOTABLE_UNCERTAIN | BOOTABLE_UNLIKELY
    """
    k = validate_kernel_presence(boot_status)
    i = validate_initramfs_presence(boot_status)
    codes = list(boot_status.get("codes") or [])
    bclass = "BOOTABLE_LIKELY"
    reasons: list[str] = []

    if not k["ok"]:
        bclass = "BOOTABLE_UNLIKELY"
        reasons.append(k["code"])
    elif not i["ok"]:
        bclass = "BOOTABLE_UNCERTAIN"
        reasons.append(i["code"])

    if not fstab_map.get("ok", True):
        if bclass == "BOOTABLE_LIKELY":
            bclass = "BOOTABLE_UNCERTAIN"
        reasons.append(fstab_map.get("code") or "fstab")

    if "rescue.boot.kernel_missing" in codes:
        bclass = "BOOTABLE_UNLIKELY"
    if "rescue.boot.boot_dir_missing" in codes:
        bclass = "BOOTABLE_UNLIKELY"

    if not bootloader.get("codes"):
        pass
    elif "rescue.bootability.bootloader_context_uncertain" in bootloader.get("codes", []):
        if bclass == "BOOTABLE_LIKELY":
            bclass = "BOOTABLE_UNCERTAIN"
        reasons.append("rescue.bootability.bootloader_context_uncertain")

    return {
        "bootability_class": bclass,
        "reason_codes": reasons,
        "kernel": k,
        "initramfs": i,
    }


def simulate_boot_preconditions(extracted_root: str | Path, *, runner: Runner = None) -> dict[str, Any]:
    """Kombiniert Layout, fstab-Mapping, Bootloader-Heuristik und Schätzung."""
    root = Path(extracted_root)
    boot_status = inspect_restored_boot_layout(root, runner=runner)
    fstab_map = validate_fstab_mapping(root, runner=runner)
    bl = validate_bootloader_requirements(boot_status, root)
    est = estimate_bootability(boot_status, fstab_map, bl)
    return {
        "boot_status": boot_status,
        "fstab_mapping": fstab_map,
        "bootloader": bl,
        "estimate": est,
    }


__all__ = [
    "estimate_bootability",
    "inspect_restored_boot_layout",
    "simulate_boot_preconditions",
    "validate_bootloader_requirements",
    "validate_fstab_mapping",
    "validate_initramfs_presence",
    "validate_kernel_presence",
]
