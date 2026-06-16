"""RS-001 stick acceptance evaluation — read-only, no USB writes."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from core.rescue_fat32_esp_usb_verify import (
    evaluate_verify_probe,
    lsblk_field,
    probe_fat_volume_label,
    probe_parent_signature_types,
    validate_fat32_esp_grub_cfg_file,
)
from core.rescue_squashfs_react_shell_verify import squashfs_verify_launcher_payload
from rescue.rescue_grub_branding import (
    BOOTX64_GFX_MODULES,
    GRUB_THEME_DIR_REL,
    GRUB_THEME_FILE,
    grub_cfg_loads_gfx_modules,
    grub_cfg_references_theme,
    validate_fat32_grub_branding,
)
from rescue.rescue_ui_launcher_contract import (
    evaluate_workspace_launcher_contract,
    validate_launcher_script_contract,
    validate_network_scripts_contract,
)

ACCEPTANCE_EXIT_OK = 0
ACCEPTANCE_EXIT_TARGET_INVALID = 10
ACCEPTANCE_EXIT_LAYOUT_INVALID = 11
ACCEPTANCE_EXIT_SQUASHFS_HASH = 12
ACCEPTANCE_EXIT_SQUASHFS_CONTENT = 13
ACCEPTANCE_EXIT_GRUB_BRANDING = 14
ACCEPTANCE_EXIT_LAUNCHER = 15
ACCEPTANCE_EXIT_FALLBACK_TUI = 16
ACCEPTANCE_EXIT_NETWORK_MENU = 17
ACCEPTANCE_EXIT_REVIEW = 20
ACCEPTANCE_EXIT_BLOCKED = 30

REQUIRED_LAYOUT_FILES: tuple[str, ...] = (
    "EFI/BOOT/BOOTX64.EFI",
    "boot/grub/grub.cfg",
    "live/vmlinuz",
    "live/initrd.img",
    "live/filesystem.squashfs",
    "setuphelfer/rescue/boot-branding.txt",
)

FORBIDDEN_TARGETS: tuple[str, ...] = ("/dev/sda",)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _unsquashfs_cat(squashfs_path: Path, member: str) -> str:
    proc = subprocess.run(
        ["unsquashfs", "-force", "-no-xattrs", "-cat", str(squashfs_path), member],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return proc.stdout if proc.returncode == 0 else ""


def target_blocked(target_device: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if target_device in FORBIDDEN_TARGETS:
        errors.append(f"FORBIDDEN_TARGET:{target_device}")
    if target_device.startswith("/dev/nvme"):
        errors.append("FORBIDDEN_NVME_TARGET")
    return bool(errors), errors


def evaluate_fat32_layout(mount_root: Path) -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_LAYOUT_FILES if not (mount_root / rel).is_file()]
    grub_cfg = mount_root / "boot/grub/grub.cfg"
    grub_text = grub_cfg.read_text(encoding="utf-8") if grub_cfg.is_file() else ""
    grub_ok = "Setuphelfer Rettung starten" in grub_text
    return {
        "layout_ok": not missing and grub_ok,
        "missing_files": missing,
        "grub_menu_entry_ok": grub_ok,
        "grub_has_root_search": "search" in grub_text.lower(),
    }


def evaluate_squashfs_hash(squashfs_path: Path, expected_sha256: str) -> dict[str, Any]:
    if not squashfs_path.is_file():
        return {"hash_ok": False, "error": "SQUASHFS_MISSING"}
    actual = sha256_file(squashfs_path)
    return {
        "hash_ok": actual.lower() == expected_sha256.lower(),
        "actual_sha256": actual,
        "expected_sha256": expected_sha256,
    }


def evaluate_squashfs_content(squashfs_path: Path) -> dict[str, Any]:
    if not shutil.which("unsquashfs"):
        return {
            "content_ok": False,
            "blocked": True,
            "reason": "unsquashfs_missing",
            "errors": ["UNSQUASHFS_TOOL_MISSING"],
        }
    verify = squashfs_verify_launcher_payload(squashfs_path)
    version_text = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/VERSION").strip()
    errors: list[str] = []
    if not verify.get("contains_react_rescue_shell"):
        errors.append("REACT_RESCUE_SHELL_INCOMPLETE")
    if not verify.get("contains_fallback_tui"):
        errors.append("FALLBACK_TUI_MISSING")
    if verify.get("network_boot_autostart"):
        errors.append("NETWORK_BOOT_AUTOSTART")
    if verify.get("telemetry_boot_autostart"):
        errors.append("TELEMETRY_BOOT_AUTOSTART")
    if not verify.get("contains_network_boot_skip"):
        errors.append("NETWORK_BOOT_SKIP_MISSING")
    if not verify.get("contains_wait_online_neutralization"):
        errors.append("WAIT_ONLINE_NEUTRALIZATION_MISSING")
    return {
        "content_ok": not errors,
        "version_in_squashfs": version_text or None,
        "verify": verify,
        "errors": errors,
    }


def evaluate_grub_branding_on_mount(mount_root: Path) -> dict[str, Any]:
    grub_cfg_path = mount_root / "boot/grub/grub.cfg"
    grub_text = grub_cfg_path.read_text(encoding="utf-8") if grub_cfg_path.is_file() else ""
    theme_dir = mount_root / GRUB_THEME_DIR_REL
    theme_file = theme_dir / GRUB_THEME_FILE
    theme_txt = theme_file.read_text(encoding="utf-8") if theme_file.is_file() else ""
    desktop_match = re.search(r'desktop-image:\s*"([^"]+)"', theme_txt)
    desktop_name = desktop_match.group(1) if desktop_match else ""
    bg_file = theme_dir / desktop_name if desktop_name else theme_dir
    image_format = "jpeg" if desktop_name.endswith(".jpg") else "png"
    errors = validate_fat32_grub_branding(mount_root, grub_text, image_format=image_format)
    evidence_path = mount_root / "setuphelfer/rescue/evidence.json"
    bootx64_modules: list[str] = []
    if evidence_path.is_file():
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            bootx64_modules = list(evidence.get("bootx64_modules_requested") or [])
        except json.JSONDecodeError:
            errors.append("EVIDENCE_JSON_INVALID")
    if bootx64_modules:
        missing = [m for m in BOOTX64_GFX_MODULES if m not in bootx64_modules]
        if missing:
            errors.append(f"BOOTX64_GFX_MODULES_MISSING:{','.join(missing)}")
    return {
        "branding_ok": not errors,
        "theme_dir_exists": theme_dir.is_dir(),
        "theme_txt_exists": theme_file.is_file(),
        "background_exists": bg_file.is_file() if desktop_name else False,
        "grub_references_theme": grub_cfg_references_theme(grub_text),
        "grub_loads_gfx": grub_cfg_loads_gfx_modules(grub_text, image_format=image_format),
        "errors": errors,
    }


def evaluate_launcher_contracts_from_squashfs(squashfs_path: Path) -> dict[str, Any]:
    launcher = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-ui-launch")
    network = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-network-onboarding")
    common = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-common.sh")
    if not launcher:
        return {"contract_ok": False, "errors": ["LAUNCHER_SCRIPT_MISSING_IN_SQUASHFS"]}
    launcher_result = validate_launcher_script_contract(launcher)
    network_result = validate_network_scripts_contract(network, common)
    return {
        "launcher": launcher_result,
        "network": network_result,
        "launcher_contract_ok": launcher_result["contract_ok"],
        "fallback_tui_contract_ok": launcher_result["contract_ok"],
        "network_menu_contract_ok": network_result["contract_ok"],
        "errors": launcher_result["errors"] + network_result["errors"],
    }


@dataclass
class StickAcceptanceResult:
    acceptance_status: str = "blocked"
    target_device: str = ""
    target_partition: str = ""
    exit_code: int = ACCEPTANCE_EXIT_BLOCKED
    fat32_layout_ok: bool = False
    squashfs_hash_ok: bool = False
    squashfs_content_ok: bool = False
    grub_branding_contract_ok: bool = False
    react_launcher_contract_ok: bool = False
    fallback_tui_contract_ok: bool = False
    network_menu_contract_ok: bool = False
    qemu_smoke: str = "not_run"
    hardware_retest_allowed: bool = False
    rs001_status: str = "yellow"
    level_1: str = "blocked"
    level_2: str = "blocked"
    level_3: str = "blocked"
    level_4: str = "blocked"
    level_5: str = "not_run"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "acceptance_status": self.acceptance_status,
            "target_device": self.target_device,
            "target_partition": self.target_partition,
            "fat32_layout_ok": self.fat32_layout_ok,
            "squashfs_hash_ok": self.squashfs_hash_ok,
            "squashfs_content_ok": self.squashfs_content_ok,
            "grub_branding_contract_ok": self.grub_branding_contract_ok,
            "react_launcher_contract_ok": self.react_launcher_contract_ok,
            "fallback_tui_contract_ok": self.fallback_tui_contract_ok,
            "network_menu_contract_ok": self.network_menu_contract_ok,
            "qemu_smoke": self.qemu_smoke,
            "hardware_retest_allowed": self.hardware_retest_allowed,
            "rs001_status": self.rs001_status,
            "levels": {
                "level_1_fat32_hash": self.level_1,
                "level_2_squashfs_content": self.level_2,
                "level_3_launcher_fallback": self.level_3,
                "level_4_grub_branding": self.level_4,
                "level_5_qemu_smoke": self.level_5,
            },
            "exit_code": self.exit_code,
            "warnings": self.warnings,
            "errors": self.errors,
            "details": self.details,
        }


def _level_status(ok: bool, *, review: bool = False) -> str:
    if ok:
        return "ok"
    if review:
        return "review_required"
    return "blocked"


def evaluate_stick_acceptance(
    *,
    mount_root: Path,
    target_device: str,
    target_partition: str,
    expected_squashfs_sha256: str,
    repo_root: Path | None = None,
    qemu_smoke: str = "not_run",
) -> StickAcceptanceResult:
    result = StickAcceptanceResult(
        target_device=target_device,
        target_partition=target_partition,
        qemu_smoke=qemu_smoke,
        level_5=qemu_smoke if qemu_smoke != "not_run" else "not_run",
    )

    blocked, block_errors = target_blocked(target_device)
    if blocked:
        result.errors.extend(block_errors)
        result.exit_code = ACCEPTANCE_EXIT_TARGET_INVALID
        result.acceptance_status = "blocked"
        return result

    probe = evaluate_verify_probe(
        parent_pttype=lsblk_field(target_device, "PTTYPE"),
        parent_signature_types=probe_parent_signature_types(target_device),
        part_parttype=lsblk_field(target_partition, "PARTTYPE"),
        part_partlabel=lsblk_field(target_partition, "PARTLABEL"),
        part_fstype=lsblk_field(target_partition, "FSTYPE"),
        part_fat_label=probe_fat_volume_label(target_partition),
        target_device=target_device,
    )
    if not probe.get("ok"):
        result.errors.extend(e["code"] for e in probe.get("errors") or [])
        result.exit_code = ACCEPTANCE_EXIT_TARGET_INVALID
        result.acceptance_status = "blocked"
        result.details["verify_probe"] = probe
        return result

    layout = evaluate_fat32_layout(mount_root)
    result.fat32_layout_ok = layout["layout_ok"]
    result.level_1 = _level_status(result.fat32_layout_ok)
    if not result.fat32_layout_ok:
        result.errors.extend(layout.get("missing_files") or [])
        if not layout.get("grub_menu_entry_ok"):
            result.errors.append("GRUB_MENU_ENTRY_MISSING")

    squashfs_path = mount_root / "live/filesystem.squashfs"
    hash_eval = evaluate_squashfs_hash(squashfs_path, expected_squashfs_sha256)
    result.squashfs_hash_ok = hash_eval.get("hash_ok", False)
    if not result.squashfs_hash_ok:
        result.level_1 = "blocked"
        result.errors.append("SQUASHFS_HASH_MISMATCH")
        result.details["squashfs_hash"] = hash_eval
    elif result.fat32_layout_ok:
        result.level_1 = "ok"

    content = evaluate_squashfs_content(squashfs_path)
    result.squashfs_content_ok = content.get("content_ok", False)
    result.level_2 = _level_status(
        result.squashfs_content_ok,
        review=content.get("blocked", False),
    )
    if content.get("blocked"):
        result.warnings.append("squashfs_content_blocked_missing_unsquashfs")
    elif not result.squashfs_content_ok:
        result.errors.extend(content.get("errors") or [])
    result.details["squashfs_content"] = content

    branding = evaluate_grub_branding_on_mount(mount_root)
    result.grub_branding_contract_ok = branding.get("branding_ok", False)
    result.level_4 = _level_status(result.grub_branding_contract_ok, review=True)
    if not result.grub_branding_contract_ok:
        result.errors.extend(branding.get("errors") or [])
    result.details["grub_branding"] = branding

    contracts = evaluate_launcher_contracts_from_squashfs(squashfs_path)
    result.react_launcher_contract_ok = contracts.get("launcher_contract_ok", False)
    result.fallback_tui_contract_ok = contracts.get("fallback_tui_contract_ok", False)
    result.network_menu_contract_ok = contracts.get("network_menu_contract_ok", False)
    level_3_ok = (
        result.react_launcher_contract_ok
        and result.fallback_tui_contract_ok
        and result.network_menu_contract_ok
    )
    result.level_3 = _level_status(level_3_ok, review=True)
    if not level_3_ok:
        result.errors.extend(contracts.get("errors") or [])
    result.details["squashfs_contracts"] = contracts

    if repo_root is not None:
        ws = evaluate_workspace_launcher_contract(repo_root)
        result.details["workspace_contract"] = ws
        if ws.get("contract_ok") and not level_3_ok:
            result.warnings.append(
                "workspace_passes_contract_but_stick_squashfs_outdated_rebuild_required"
            )

    stick_logs = list(mount_root.glob("setuphelfer/logs/**/*"))
    stick_evidence = list(mount_root.glob("setuphelfer/evidence/**/*"))
    result.details["stick_logs_on_esp"] = {
        "logs_files": [str(p.relative_to(mount_root)) for p in stick_logs if p.is_file()],
        "evidence_files": [str(p.relative_to(mount_root)) for p in stick_evidence if p.is_file()],
        "logs_present": any(p.is_file() for p in stick_logs),
    }
    if not result.details["stick_logs_on_esp"]["logs_present"]:
        result.warnings.append("no_operator_logs_on_stick_esp_readback")

    levels_green = (
        result.level_1 == "ok"
        and result.level_2 == "ok"
        and result.level_3 == "ok"
        and result.level_4 == "ok"
    )
    result.hardware_retest_allowed = levels_green
    result.rs001_status = "yellow"

    if not result.fat32_layout_ok or not result.squashfs_hash_ok:
        result.acceptance_status = "blocked"
        result.exit_code = (
            ACCEPTANCE_EXIT_LAYOUT_INVALID
            if not result.fat32_layout_ok
            else ACCEPTANCE_EXIT_SQUASHFS_HASH
        )
    elif not result.squashfs_content_ok:
        result.acceptance_status = "blocked" if not content.get("blocked") else "review_required"
        result.exit_code = (
            ACCEPTANCE_EXIT_REVIEW if content.get("blocked") else ACCEPTANCE_EXIT_SQUASHFS_CONTENT
        )
    elif not level_3_ok or not result.grub_branding_contract_ok:
        result.acceptance_status = "review_required"
        if not result.grub_branding_contract_ok:
            result.exit_code = ACCEPTANCE_EXIT_GRUB_BRANDING
        elif not result.network_menu_contract_ok:
            result.exit_code = ACCEPTANCE_EXIT_NETWORK_MENU
        elif not result.fallback_tui_contract_ok:
            result.exit_code = ACCEPTANCE_EXIT_FALLBACK_TUI
        else:
            result.exit_code = ACCEPTANCE_EXIT_LAUNCHER
    else:
        result.acceptance_status = "ok"
        result.exit_code = ACCEPTANCE_EXIT_OK

    if result.acceptance_status == "review_required" and result.exit_code < ACCEPTANCE_EXIT_REVIEW:
        result.exit_code = ACCEPTANCE_EXIT_REVIEW

    return result
