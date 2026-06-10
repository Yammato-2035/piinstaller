"""FAT32 ESP GRUB branding update — theme/grub.cfg/BOOTX64 only (no partition rewrite)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from core.rescue_fat32_esp_payload_update import validate_payload_update_target_probe
from core.rescue_fat32_esp_usb_writer import (
    build_fat32_esp_bootx64_efi,
    generate_fat32_esp_grub_cfg,
    sha256_file,
)
from rescue.rescue_grub_branding import stage_grub_theme_to_fat32_staging, validate_fat32_grub_branding

CONFIRM_PHRASE_GRUB_BRANDING = "UPDATE SETUPHELFER FAT32 ESP GRUB BRANDING"

ALLOWED_GRUB_BRANDING_REL_PATHS: tuple[str, ...] = (
    "boot/grub/grub.cfg",
    "boot/grub/themes/setuphelfer/theme.txt",
    "boot/grub/themes/setuphelfer/setuphelfer-boot-menu-de.png",
    "EFI/BOOT/BOOTX64.EFI",
    "setuphelfer/rescue/evidence.json",
    "setuphelfer/rescue/boot-branding.txt",
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def script_has_forbidden_destructive_commands(script_text: str) -> list[str]:
    from core.rescue_fat32_esp_payload_update import script_has_forbidden_destructive_commands as _fn

    return _fn(script_text)


def build_grub_branding_update_plan(
    *,
    target_device: str,
    confirm_phrase: str | None,
    confirm_update: bool,
    execute_update: bool,
    safety: Mapping[str, Any],
    allow_mounted: bool = False,
) -> dict[str, Any]:
    """Plan GRUB branding update — same safety probe as payload update."""
    blockers: list[str] = list(safety.get("blockers") or [])
    if safety.get("blocked"):
        blockers = list(dict.fromkeys(blockers))
    if not allow_mounted and "PARTITION_MOUNTED" in blockers:
        pass  # keep blocker
    elif allow_mounted:
        blockers = [b for b in blockers if b != "PARTITION_MOUNTED"]

    if confirm_update:
        if confirm_phrase != CONFIRM_PHRASE_GRUB_BRANDING:
            blockers.append("CONFIRM_PHRASE_MISMATCH")
    else:
        blockers.append("OPERATOR_CONFIRM_REQUIRED")

    if not execute_update:
        blockers = [b for b in blockers if b not in ("OPERATOR_CONFIRM_REQUIRED",)]

    blocked = bool(blockers) if execute_update else bool(safety.get("blocked")) or not confirm_update

    return {
        "target_device": target_device,
        "target_partition": safety.get("target_partition"),
        "confirm_phrase_expected": CONFIRM_PHRASE_GRUB_BRANDING,
        "grub_paths": list(ALLOWED_GRUB_BRANDING_REL_PATHS),
        "safety": dict(safety),
        "blocked": blocked,
        "blockers": blockers,
        "grub_branding_update_executed": False,
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "secrets_exposed": False,
    }


def apply_grub_branding_on_mount(
    mount_root: Path,
    *,
    repo_root: Path,
    fat_uuid: str | None,
) -> dict[str, Any]:
    """Stage theme, refresh grub.cfg, rebuild BOOTX64.EFI, refresh evidence metadata."""
    stage_meta = stage_grub_theme_to_fat32_staging(mount_root, repo_root)
    cfg_text = generate_fat32_esp_grub_cfg(fat_uuid=fat_uuid)
    grub_cfg_path = mount_root / "boot" / "grub" / "grub.cfg"
    grub_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    grub_cfg_path.write_text(cfg_text, encoding="utf-8")

    bootx64_path = mount_root / "EFI" / "BOOT" / "BOOTX64.EFI"
    bootx64_meta = build_fat32_esp_bootx64_efi(bootx64_path)

    branding_txt = mount_root / "setuphelfer" / "rescue" / "boot-branding.txt"
    branding_txt.parent.mkdir(parents=True, exist_ok=True)
    branding_txt.write_text(
        "Setuphelfer Rettungsstick — GRUB theme/branding active\n",
        encoding="utf-8",
    )

    evidence_path = mount_root / "setuphelfer" / "rescue" / "evidence.json"
    evidence: dict[str, Any] = {}
    if evidence_path.is_file():
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            evidence = {}
    evidence["bootx64_modules_requested"] = list(bootx64_meta.get("modules_requested") or [])
    evidence["bootx64_sha256"] = bootx64_meta.get("sha256")
    evidence["grub_branding_updated_at"] = _now_iso()
    evidence["grub_branding_writer_mode"] = "fat32_esp_grub_branding_update"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    grub_text = grub_cfg_path.read_text(encoding="utf-8")
    errors = validate_fat32_grub_branding(
        mount_root,
        grub_text,
        bootx64_modules=evidence.get("bootx64_modules_requested"),
    )
    return {
        "stage_meta": stage_meta,
        "bootx64_meta": bootx64_meta,
        "grub_cfg_path": str(grub_cfg_path),
        "grub_cfg_sha256": sha256_file(grub_cfg_path),
        "bootx64_sha256": bootx64_meta.get("sha256"),
        "branding_ok": not errors,
        "errors": errors,
    }


def build_grub_branding_update_result(
    *,
    target_device: str,
    started_at: str,
    completed_at: str,
    grub_branding_update_executed: bool,
    grub_branding_update_status: str,
    verify_status: str,
    evidence_dir: str,
    apply_result: Mapping[str, Any] | None = None,
    failed_step: str | None = None,
) -> dict[str, Any]:
    apply_result = apply_result or {}
    return {
        "grub_branding_update_schema_version": 1,
        "target_device": target_device,
        "started_at": started_at,
        "completed_at": completed_at,
        "grub_branding_update_executed": grub_branding_update_executed,
        "grub_branding_update_status": grub_branding_update_status,
        "verify_status": verify_status,
        "branding_ok": apply_result.get("branding_ok", False),
        "errors": apply_result.get("errors") or [],
        "bootx64_sha256": apply_result.get("bootx64_sha256"),
        "grub_cfg_sha256": apply_result.get("grub_cfg_sha256"),
        "evidence_dir": evidence_dir,
        "failed_step": failed_step,
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "secrets_exposed": False,
        "no_fake_green": True,
        "rs001_status": "yellow",
    }


__all__ = [
    "ALLOWED_GRUB_BRANDING_REL_PATHS",
    "CONFIRM_PHRASE_GRUB_BRANDING",
    "apply_grub_branding_on_mount",
    "build_grub_branding_update_plan",
    "build_grub_branding_update_result",
    "validate_payload_update_target_probe",
]
