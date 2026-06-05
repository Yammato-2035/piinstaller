"""Rescue ISO UEFI-x64 boot classification (read-only, no ISO mutation)."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

UEFI_ERROR_CODES = {
    "efi_boot_files_missing": "RESCUE-UEFI-001",
    "efi_eltorito_entry_missing": "RESCUE-UEFI-002",
    "isolinux_only_iso": "RESCUE-UEFI-003",
    "msi_uefi_boot_failed_confirmed": "RESCUE-UEFI-004",
    "windows_inspect_blocked_by_rescue_uefi_boot": "RESCUE-UEFI-005",
}

ISO_CLASSIFICATIONS = (
    "uefi_x64_boot_ready",
    "iso_bios_hybrid_bootable_only",
    "uefi_boot_path_missing",
    "efi_boot_files_missing",
    "isolinux_only_iso",
)


@dataclass(frozen=True)
class UefiIsoSignals:
    iso_exists: bool
    sha256: str | None
    has_bios_boot: bool
    has_efi_eltorito: bool
    has_bootx64_efi: bool
    xorriso_report_excerpt: str


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _sha256(path: Path) -> str | None:
    proc = _run(["sha256sum", str(path)])
    if proc.returncode != 0:
        return None
    return proc.stdout.split()[0] if proc.stdout.strip() else None


def _xorriso_report(iso: Path) -> str:
    proc = _run(["xorriso", "-indev", str(iso), "-report_el_torito", "as_mkisofs"])
    return proc.stdout if proc.returncode == 0 else proc.stderr


def _xorriso_find(iso: Path, path: str, name: str | None = None) -> bool:
    cmd = ["xorriso", "-osirrox", "on", "-indev", str(iso), "-find", path]
    if name:
        cmd.extend(["-name", name])
    proc = _run(cmd)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def collect_uefi_iso_signals(iso_path: Path) -> UefiIsoSignals:
    if not iso_path.is_file():
        return UefiIsoSignals(False, None, False, False, False, "")

    report = _xorriso_report(iso_path)
    has_bios = bool(re.search(r"isolinux\.bin|/boot/grub/grub_eltorito", report))
    has_efi = bool(
        re.search(
            r"efi\.img|BOOTX64\.EFI|grubx64\.efi|shimx64\.efi|append_partition.*0xef|appended_part_as_gpt",
            report,
            re.I,
        )
    )
    has_bootx64 = _xorriso_find(iso_path, "/EFI/BOOT", "BOOTX64.EFI")
    if not has_bootx64:
        for candidate in ("/boot/grub/BOOTX64.EFI", "/EFI/BOOT/grubx64.efi", "/EFI/BOOT/shimx64.efi"):
            if _xorriso_find(iso_path, candidate):
                has_bootx64 = True
                break

    excerpt = "\n".join(report.splitlines()[:20])
    return UefiIsoSignals(
        iso_exists=True,
        sha256=_sha256(iso_path),
        has_bios_boot=has_bios,
        has_efi_eltorito=has_efi,
        has_bootx64_efi=has_bootx64,
        xorriso_report_excerpt=excerpt,
    )


def classify_uefi_iso(signals: UefiIsoSignals) -> dict[str, Any]:
    errors: list[str] = []
    tags: list[str] = []

    if not signals.iso_exists:
        errors.extend(["efi_boot_files_missing", "uefi_boot_path_missing"])
        return _result("missing_iso", errors, tags, signals)

    if signals.has_bios_boot and not signals.has_efi_eltorito and not signals.has_bootx64_efi:
        errors.extend(["isolinux_only_iso", "efi_eltorito_entry_missing", "efi_boot_files_missing"])
        tags.extend(
            [
                "isolinux_only_iso",
                "iso_bios_hybrid_bootable_only",
                "uefi_boot_path_missing",
                "efi_boot_files_missing",
            ]
        )
        return _result("isolinux_only_iso", errors, tags, signals)

    if not signals.has_bootx64_efi:
        errors.append("efi_boot_files_missing")
        tags.append("efi_boot_files_missing")

    if not signals.has_efi_eltorito:
        errors.append("efi_eltorito_entry_missing")
        tags.append("uefi_boot_path_missing")

    if errors:
        return _result("uefi_boot_incomplete", errors, tags, signals)

    return _result("uefi_x64_boot_ready", [], ["uefi_x64_boot_ready"], signals)


def _result(status: str, errors: list[str], tags: list[str], signals: UefiIsoSignals) -> dict[str, Any]:
    unique_errors = list(dict.fromkeys(errors))
    unique_tags = list(dict.fromkeys(tags))
    return {
        "status": status,
        "uefi_boot_ready": status == "uefi_x64_boot_ready",
        "classifications": unique_tags,
        "errors": [
            {"id": key, "code": UEFI_ERROR_CODES[key]}
            for key in unique_errors
            if key in UEFI_ERROR_CODES
        ],
        "signals": {
            "iso_exists": signals.iso_exists,
            "sha256": signals.sha256,
            "has_bios_boot": signals.has_bios_boot,
            "has_efi_eltorito": signals.has_efi_eltorito,
            "has_bootx64_efi": signals.has_bootx64_efi,
            "xorriso_report_excerpt": signals.xorriso_report_excerpt,
        },
    }


def load_gate_overlay(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def classify_rescue_uefi_gate(
    *,
    iso_path: Path,
    gate_status_path: Path | None = None,
) -> dict[str, Any]:
    iso = classify_uefi_iso(collect_uefi_iso_signals(iso_path))
    overlay = load_gate_overlay(gate_status_path) if gate_status_path else {}

    blockers: list[dict[str, Any]] = []
    if not iso["uefi_boot_ready"]:
        blockers.append(
            {
                "id": "RESCUE_ISO_UEFI_X64_NOT_READY",
                "severity": "critical",
                "status": "blocked",
                "codes": [e["code"] for e in iso["errors"]],
            }
        )

    if overlay.get("target_uefi_boot_validated") is False or overlay.get("msi_uefi_boot_failed_confirmed"):
        iso.setdefault("classifications", []).append("msi_uefi_boot_failed_confirmed")
        blockers.append(
            {
                "id": "RESCUE_USB_UEFI_BOOT_FAILURE_MSI_WINDOWS11",
                "severity": "critical",
                "status": "blocked",
                "code": UEFI_ERROR_CODES["msi_uefi_boot_failed_confirmed"],
            }
        )

    windows_inspect_executable = bool(iso["uefi_boot_ready"]) and len(blockers) == 0
    if not windows_inspect_executable:
        iso.setdefault("classifications", []).append("windows_inspect_blocked_by_rescue_uefi_boot")

    return {
        "schema_version": 1,
        "iso_path": str(iso_path),
        "iso_classification": iso,
        "blockers": blockers,
        "windows_inspect_executable": windows_inspect_executable,
        "next_prompt_id": "RESCUE_ISO_UEFI_X64_REBUILD_OPERATOR_RUN"
        if not iso["uefi_boot_ready"]
        else overlay.get("next_prompt_id"),
    }
