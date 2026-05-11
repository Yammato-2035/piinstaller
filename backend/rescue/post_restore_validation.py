from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _check(code: str, ok: bool) -> dict[str, Any]:
    return {"code": code, "ok": bool(ok)}


def _glob_any(base: Path, patterns: list[str]) -> bool:
    for pat in patterns:
        if list(base.glob(pat)):
            return True
    return False


def validate_restored_target(target_path: str) -> dict[str, Any]:
    """Post-Restore-Validierung, rein lesend."""
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    root = Path(str(target_path or "")).expanduser()

    exists = root.exists()
    checks.append(_check("target_path_exists", exists))
    if not exists:
        errors.append("POST_RESTORE_TARGET_MISSING")
        return {
            "status": "failed",
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
            "boot": {
                "code": "POST_RESTORE_FAILED",
                "boot_repair_recommended": False,
                "kernel_artifact_present": False,
                "initramfs_artifact_present": False,
            },
            "setuphelfer": {
                "backend_unit_present": False,
                "install_path_present": False,
            },
        }

    readable = os.access(root, os.R_OK | os.X_OK)
    checks.append(_check("target_path_readable", readable))
    if not readable:
        errors.append("POST_RESTORE_TARGET_NOT_READABLE")
        return {
            "status": "failed",
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
            "boot": {
                "code": "POST_RESTORE_FAILED",
                "boot_repair_recommended": False,
                "kernel_artifact_present": False,
                "initramfs_artifact_present": False,
            },
            "setuphelfer": {
                "backend_unit_present": False,
                "install_path_present": False,
            },
        }

    etc_exists = (root / "etc").is_dir()
    usr_exists = (root / "usr").is_dir()
    var_exists = (root / "var").is_dir()
    home_exists = (root / "home").is_dir()
    boot_dir_exists = (root / "boot").is_dir()

    checks.append(_check("etc_exists", etc_exists))
    checks.append(_check("usr_exists", usr_exists))
    checks.append(_check("var_exists", var_exists))
    checks.append(_check("home_exists_or_not_required", home_exists))
    checks.append(_check("boot_dir_exists", boot_dir_exists))

    if not etc_exists:
        errors.append("POST_RESTORE_ETC_MISSING")
    if not usr_exists:
        errors.append("POST_RESTORE_USR_MISSING")
    if not var_exists:
        errors.append("POST_RESTORE_VAR_MISSING")
    if not home_exists:
        warnings.append("POST_RESTORE_HOME_MISSING")

    fstab_exists = (root / "etc" / "fstab").is_file()
    checks.append(_check("fstab_exists", fstab_exists))
    if not fstab_exists:
        warnings.append("POST_RESTORE_FSTAB_MISSING")

    kernel_present = _glob_any(root / "boot", ["vmlinuz*", "Image*"]) if boot_dir_exists else False
    initramfs_present = _glob_any(root / "boot", ["initrd*", "initramfs*"]) if boot_dir_exists else False
    checks.append(_check("kernel_artifact_present", kernel_present))
    checks.append(_check("initramfs_artifact_present", initramfs_present))

    if not boot_dir_exists:
        warnings.append("POST_RESTORE_BOOT_DIR_MISSING")
    if not kernel_present:
        warnings.append("POST_RESTORE_KERNEL_MISSING")
    if not initramfs_present:
        warnings.append("POST_RESTORE_INITRAMFS_MISSING")

    unit_present = (root / "etc" / "systemd" / "system" / "setuphelfer-backend.service").is_file()
    install_path_present = (root / "opt" / "setuphelfer").exists()
    checks.append(_check("setuphelfer_backend_unit_present", unit_present))
    checks.append(_check("setuphelfer_install_path_present", install_path_present))
    if not unit_present:
        warnings.append("POST_RESTORE_SETUPHELPER_UNIT_MISSING")
    if not install_path_present:
        warnings.append("POST_RESTORE_SETUPHELPER_PATH_MISSING")

    boot_repair_recommended = (not kernel_present) or (not initramfs_present) or (not boot_dir_exists)
    if boot_repair_recommended:
        warnings.append("POST_RESTORE_BOOT_REPAIR_RECOMMENDED")

    status = "valid"
    if errors:
        status = "failed"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "boot": {
            "code": "POST_RESTORE_VALID" if status == "valid" else ("POST_RESTORE_FAILED" if status == "failed" else "POST_RESTORE_WARNING"),
            "boot_repair_recommended": boot_repair_recommended,
            "kernel_artifact_present": kernel_present,
            "initramfs_artifact_present": initramfs_present,
        },
        "setuphelfer": {
            "backend_unit_present": unit_present,
            "install_path_present": install_path_present,
        },
    }
