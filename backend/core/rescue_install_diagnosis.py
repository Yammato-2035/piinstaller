"""Install diagnosis — classify prior install failures (PI-RS-INSTALL-ASSISTANT-001).

Read-only. No BIOS flash. Telemetry must use existing redacted assessment upload paths.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


class InstallIssueCode(str, Enum):
    BIOS_OUTDATED_LIKELY = "bios_outdated_likely"
    PCIE_AER_FLOOD_BLOCKS_INSTALLER = "pcie_aer_flood_blocks_installer"
    SECURE_BOOT_BLOCKS_UNSIGNED_ISO = "secure_boot_blocks_unsigned_iso"
    WRONG_BOOT_DEVICE_SELECTED = "wrong_boot_device_selected"
    NVME_NOT_VISIBLE_IN_INSTALLER = "nvme_not_visible_in_installer"
    INSTALLER_MEDIA_CORRUPT = "installer_media_corrupt"
    DISK_ROLE_AMBIGUOUS = "disk_role_ambiguous"


ISSUE_META: dict[str, dict[str, str]] = {
    InstallIssueCode.BIOS_OUTDATED_LIKELY.value: {
        "severity": "high",
        "next_action_de": "Offizielle BIOS-Version prüfen (nur lesen); kein Auto-Flash.",
        "next_action_en": "Compare official BIOS version (read-only); no auto-flash.",
        "ampel": "yellow",
    },
    InstallIssueCode.PCIE_AER_FLOOD_BLOCKS_INSTALLER.value: {
        "severity": "critical",
        "next_action_de": "PCIe AER-Flut klären bevor Installer erneut gestartet wird.",
        "next_action_en": "Resolve PCIe AER flood before restarting the installer.",
        "ampel": "red",
    },
    InstallIssueCode.SECURE_BOOT_BLOCKS_UNSIGNED_ISO.value: {
        "severity": "high",
        "next_action_de": "Secure Boot / signierte Medien prüfen oder Secure Boot temporär laut Anleitung.",
        "next_action_en": "Check Secure Boot / signed media or follow Secure Boot checklist.",
        "ampel": "yellow",
    },
    InstallIssueCode.WRONG_BOOT_DEVICE_SELECTED.value: {
        "severity": "high",
        "next_action_de": "Boot-Gerät erneut wählen: Rescue-Stick bzw. Ziel-NVMe, nicht Windows-NVMe.",
        "next_action_en": "Reselect boot device: rescue stick or linux_target NVMe, not Windows NVMe.",
        "ampel": "yellow",
    },
    InstallIssueCode.NVME_NOT_VISIBLE_IN_INSTALLER.value: {
        "severity": "critical",
        "next_action_de": "NVMe-Sichtbarkeit / VMD/RST und Rollenbindung prüfen.",
        "next_action_en": "Check NVMe visibility / VMD/RST and disk role binding.",
        "ampel": "red",
    },
    InstallIssueCode.INSTALLER_MEDIA_CORRUPT.value: {
        "severity": "critical",
        "next_action_de": "ISO SHA256 erneut verifizieren und Cache ersetzen.",
        "next_action_en": "Re-verify ISO SHA256 and replace cache.",
        "ampel": "red",
    },
    InstallIssueCode.DISK_ROLE_AMBIGUOUS.value: {
        "severity": "critical",
        "next_action_de": "Disk-Rollen neu binden (serial_hash), nie nur /dev/nvmeXnY.",
        "next_action_en": "Re-bind disk roles (serial_hash), never /dev/nvmeXnY alone.",
        "ampel": "red",
    },
}


def _ampel_rank(ampel: str) -> int:
    return {"green": 0, "yellow": 1, "red": 2}.get(ampel, 0)


def build_install_diagnosis(
    *,
    assessment: Mapping[str, Any] | None = None,
    disk_roles: Mapping[str, Any] | None = None,
    bios_compare: Mapping[str, Any] | None = None,
    iso_status: Mapping[str, Any] | None = None,
    secure_boot_enabled: bool | None = None,
    boot_device_role: str | None = None,
    nvme_visible_in_installer: bool | None = None,
    aer_flood: bool | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    """Condense Assessment V2 + roles + BIOS compare into install issue codes."""
    issues: list[dict[str, Any]] = []
    assessment = assessment or {}
    disk_roles = disk_roles or {}
    bios_compare = bios_compare or {}
    iso_status = iso_status or {}

    # AER from assessment or explicit flag
    aer = aer_flood
    if aer is None:
        codes = set(str(c) for c in (assessment.get("issue_codes") or []))
        findings = assessment.get("findings") or assessment.get("pcie_aer") or {}
        if "pcie_aer_fatal" in codes or "pcie_aer_nonfatal" in codes:
            aer = True
        elif isinstance(findings, Mapping) and (
            findings.get("fatal_count") or findings.get("flood") or findings.get("blocks_installer")
        ):
            aer = True
    if aer:
        issues.append(_issue(InstallIssueCode.PCIE_AER_FLOOD_BLOCKS_INSTALLER, locale))

    if bios_compare.get("status") == "update_available":
        issues.append(_issue(InstallIssueCode.BIOS_OUTDATED_LIKELY, locale))

    if secure_boot_enabled is True and iso_status.get("signature_ok") is False:
        issues.append(_issue(InstallIssueCode.SECURE_BOOT_BLOCKS_UNSIGNED_ISO, locale))

    if boot_device_role in {"windows", "windows_system", "wrong"}:
        issues.append(_issue(InstallIssueCode.WRONG_BOOT_DEVICE_SELECTED, locale))

    if nvme_visible_in_installer is False:
        issues.append(_issue(InstallIssueCode.NVME_NOT_VISIBLE_IN_INSTALLER, locale))

    if iso_status.get("status") == "corrupt" or iso_status.get("sha256_ok") is False and iso_status.get(
        "status"
    ) not in {None, "missing", "ready_for_distro_selection"}:
        if iso_status.get("status") == "corrupt":
            issues.append(_issue(InstallIssueCode.INSTALLER_MEDIA_CORRUPT, locale))

    targets_ok = disk_roles.get("targets_distinct")
    resolve_ok = disk_roles.get("ok")
    if targets_ok is False or resolve_ok is False or disk_roles.get("ambiguous"):
        issues.append(_issue(InstallIssueCode.DISK_ROLE_AMBIGUOUS, locale))

    ampel = "green"
    for iss in issues:
        if _ampel_rank(iss["ampel"]) > _ampel_rank(ampel):
            ampel = iss["ampel"]

    next_action = None
    if issues:
        # highest severity first
        ordered = sorted(issues, key=lambda i: -_ampel_rank(i["ampel"]))
        next_action = ordered[0].get("next_action")

    return {
        "schema_version": 1,
        "contract": "install_diagnosis_v1",
        "ampel": ampel,
        "status": "ok" if ampel == "green" else "issues_found",
        "issues": issues,
        "issue_codes": [i["code"] for i in issues],
        "next_action": next_action,
        "bios_flash_allowed": False,
        "write_allowed": False,
        "telemetry": {
            "upload_path": "assessment_v2_redacted",
            "pii_allowed": False,
            "dry_run_local_ok": True,
        },
        "evidence_subdir": "install-diagnosis",
    }


def _issue(code: InstallIssueCode, locale: str) -> dict[str, Any]:
    meta = ISSUE_META[code.value]
    action_key = "next_action_de" if locale.startswith("de") else "next_action_en"
    return {
        "code": code.value,
        "severity": meta["severity"],
        "ampel": meta["ampel"],
        "next_action": meta[action_key],
    }


def redact_install_diagnosis_for_upload(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    """Strip anything that could carry serials/paths beyond hashes already present."""
    safe_issues = []
    for iss in list(diagnosis.get("issues") or []):
        if not isinstance(iss, Mapping):
            continue
        safe_issues.append(
            {
                "code": iss.get("code"),
                "severity": iss.get("severity"),
                "ampel": iss.get("ampel"),
            }
        )
    return {
        "contract": "install_diagnosis_v1_redacted",
        "ampel": diagnosis.get("ampel"),
        "status": diagnosis.get("status"),
        "issue_codes": list(diagnosis.get("issue_codes") or []),
        "issues": safe_issues,
        "bios_flash_allowed": False,
        "pii_allowed": False,
    }
