from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _check(code: str, ok: bool) -> dict[str, Any]:
    return {"code": code, "ok": bool(ok)}


def _has_any(base: Path, patterns: list[str]) -> bool:
    for pat in patterns:
        if list(base.glob(pat)):
            return True
    return False


def _parse_fstab_basic(path: Path) -> tuple[bool, bool]:
    if not path.is_file():
        return False, False
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return False, False

    parseable = True
    has_uuid_ref = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            parseable = False
        if parts and (parts[0].startswith("UUID=") or parts[0].startswith("PARTUUID=")):
            has_uuid_ref = True
    return parseable, has_uuid_ref


def check_boot_capability(target_path: str, inspect_result: dict | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    boot_type_hints: list[str] = []
    risks: list[str] = []
    recommendations: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    root = Path(str(target_path or "")).expanduser()

    exists = root.exists()
    checks.append(_check("target_path_exists", exists))
    if not exists:
        errors.append("BOOT_TARGET_MISSING")
        return {
            "status": "boot_failed",
            "checks": checks,
            "boot_type_hints": boot_type_hints,
            "risks": risks,
            "recommendations": ["BOOT_MANUAL_REVIEW_RECOMMENDED"],
            "warnings": warnings,
            "errors": errors,
        }

    readable = os.access(root, os.R_OK | os.X_OK)
    checks.append(_check("target_path_readable", readable))
    if not readable:
        errors.append("BOOT_TARGET_NOT_READABLE")
        return {
            "status": "boot_failed",
            "checks": checks,
            "boot_type_hints": boot_type_hints,
            "risks": risks,
            "recommendations": ["BOOT_MANUAL_REVIEW_RECOMMENDED"],
            "warnings": warnings,
            "errors": errors,
        }

    etc_dir = root / "etc"
    etc_exists = etc_dir.is_dir()
    fstab_path = etc_dir / "fstab"
    fstab_exists = fstab_path.is_file()
    fstab_parseable, fstab_has_uuid = _parse_fstab_basic(fstab_path)

    boot_dir = root / "boot"
    boot_exists = boot_dir.is_dir()
    kernel_present = _has_any(boot_dir, ["vmlinuz*", "Image*"]) if boot_exists else False
    initramfs_present = _has_any(boot_dir, ["initrd*", "initramfs*"]) if boot_exists else False

    efi_present = (root / "boot" / "efi").is_dir() or (root / "efi").is_dir() or (root / "boot" / "EFI").is_dir()
    grub_present = (root / "boot" / "grub" / "grub.cfg").is_file() or (root / "etc" / "default" / "grub").is_file()
    rpi_present = ((root / "boot" / "config.txt").is_file() and (root / "boot" / "cmdline.txt").is_file()) or (
        (root / "boot" / "firmware" / "config.txt").is_file() and (root / "boot" / "firmware" / "cmdline.txt").is_file()
    )
    windows_bootmgr = (
        (root / "boot" / "efi" / "EFI" / "Microsoft" / "Boot" / "bootmgfw.efi").is_file()
        or (root / "EFI" / "Microsoft" / "Boot" / "bootmgfw.efi").is_file()
    )
    dualboot_present = windows_bootmgr and (kernel_present or fstab_exists or grub_present)

    checks.extend(
        [
            _check("etc_fstab_exists", fstab_exists),
            _check("fstab_parseable_basic", fstab_parseable),
            _check("fstab_references_uuid_or_partuuid", fstab_has_uuid),
            _check("boot_dir_exists", boot_exists),
            _check("kernel_artifact_present", kernel_present),
            _check("initramfs_artifact_present", initramfs_present),
            _check("efi_dir_present", efi_present),
            _check("grub_config_present", grub_present),
            _check("raspberry_pi_boot_files_present", rpi_present),
            _check("windows_bootmanager_present", windows_bootmgr),
            _check("dualboot_indicators_present", dualboot_present),
        ]
    )

    if efi_present:
        boot_type_hints.append("BOOT_EFI_HINT_FOUND")
    if grub_present:
        boot_type_hints.append("BOOT_GRUB_HINT_FOUND")
    if rpi_present:
        boot_type_hints.append("BOOT_RPI_HINT_FOUND")
    if windows_bootmgr:
        boot_type_hints.append("BOOT_WINDOWS_BOOTMANAGER_FOUND")

    if not fstab_exists:
        warnings.append("BOOT_FSTAB_MISSING")
    if fstab_exists and not fstab_parseable:
        warnings.append("BOOT_FSTAB_UNPARSEABLE")
    if fstab_exists and not fstab_has_uuid:
        warnings.append("BOOT_FSTAB_UUID_REFERENCES_MISSING")

    if not boot_exists:
        warnings.append("BOOT_DIR_MISSING")
    if not kernel_present:
        warnings.append("BOOT_KERNEL_MISSING")
    if not initramfs_present:
        warnings.append("BOOT_INITRAMFS_MISSING")

    if windows_bootmgr:
        warnings.append("BOOT_WINDOWS_BOOTMANAGER_FOUND")
        risks.append("BOOT_WINDOWS_BOOTMANAGER_FOUND")
        recommendations.append("BOOT_MANUAL_REVIEW_RECOMMENDED")
    if dualboot_present:
        warnings.append("BOOT_DUALBOOT_RISK")
        risks.append("BOOT_DUALBOOT_RISK")
        recommendations.append("BOOT_MANUAL_REVIEW_RECOMMENDED")

    if not etc_exists and not windows_bootmgr and not rpi_present:
        errors.append("BOOT_FSTAB_MISSING")

    if not boot_exists or not kernel_present or not initramfs_present or not fstab_exists:
        recommendations.append("BOOT_REPAIR_RECOMMENDED")

    status = "boot_unknown"
    if errors:
        status = "boot_failed"
    else:
        likely_trigger = fstab_exists and boot_exists and kernel_present and initramfs_present and not windows_bootmgr and not dualboot_present
        warning_trigger = (
            bool(warnings)
            or windows_bootmgr
            or dualboot_present
            or not fstab_exists
            or not boot_exists
            or not kernel_present
            or not initramfs_present
            or (fstab_exists and not fstab_has_uuid)
        )
        if likely_trigger and not warning_trigger:
            status = "boot_likely"
        elif warning_trigger:
            status = "boot_warning"

    if inspect_result and isinstance(inspect_result, dict):
        cls = inspect_result.get("classification") if isinstance(inspect_result.get("classification"), dict) else {}
        stype = str(cls.get("system_type") or "")
        if stype in {"WINDOWS", "DUALBOOT"} and "BOOT_MANUAL_REVIEW_RECOMMENDED" not in recommendations:
            recommendations.append("BOOT_MANUAL_REVIEW_RECOMMENDED")
            if status == "boot_likely":
                status = "boot_warning"

    return {
        "status": status,
        "checks": checks,
        "boot_type_hints": boot_type_hints,
        "risks": risks,
        "recommendations": recommendations,
        "warnings": warnings,
        "errors": errors,
    }
