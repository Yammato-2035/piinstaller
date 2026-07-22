"""DCC / readiness aggregation for firmware + Win11 + Linux second NVMe workflow."""

from __future__ import annotations

from typing import Any, Mapping

from core.rescue_windows11_controlled_retest import build_win11_retest_dcc

SCHEMA_VERSION = 1


def _tone(status: str | None) -> str:
    s = (status or "").lower()
    if s in {"green", "ok", "ready", "current", "valid", "healthy", "deployed", "passed"}:
        return "green"
    if s in {"yellow", "review_required", "update_available", "pending", "unknown", "insufficient_evidence"}:
        return "yellow"
    if s in {"red", "blocked", "corrupt", "failed", "unsuitable_for_install"}:
        return "red"
    return "gray"


def build_gabriel_physical_diag_dcc(
    *,
    binding: Mapping[str, Any] | None = None,
    bios: Mapping[str, Any] | None = None,
    nvme_a: Mapping[str, Any] | None = None,
    nvme_b: Mapping[str, Any] | None = None,
    windows: Mapping[str, Any] | None = None,
    endstatus: str = "diagnosis_incomplete",
) -> dict[str, Any]:
    """DCC block for Gabriel G513QM physical diagnosis (no full serials)."""
    b = dict(binding or {})
    bios_d = dict(bios or {})
    win = dict(windows or {})

    def _nvme_slot(entry: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
        e = dict(entry or {})
        tone = _tone(str(e.get("health_label") or e.get("smart_status") or "gray").lower())
        if str(e.get("health_label") or "").upper() == "CRITICAL":
            tone = "red"
        elif str(e.get("health_label") or "").upper() == "WARNING":
            tone = "yellow"
        elif str(e.get("health_label") or "").upper() == "HEALTHY":
            tone = "green"
        return {
            "label": label,
            "identity_hash_short": str(e.get("nvme_identity_hash") or e.get("serial_hash") or "")[:12],
            "serial_masked": e.get("serial_masked") or "",
            "firmware": e.get("firmware_revision") or "",
            "pci": e.get("pci_address") or "",
            "smart": e.get("health_label") or e.get("smart_status") or "GRAY",
            "role": e.get("intended_role") or "unassigned",
            "write_allowed": False,
            "tone": tone if e else "gray",
        }

    panther = win.get("panther_found")
    if panther is True:
        win_tone = "yellow"
    elif panther is False:
        win_tone = "yellow"
    else:
        win_tone = "gray"

    overall = "yellow"
    if endstatus.startswith("blocked_"):
        overall = "red"
    elif endstatus in {
        "ready_for_controlled_windows_retest_with_log_collection",
        "ready_for_windows_install_planning",
        "diagnosis_complete_windows_fix_pending",
    }:
        overall = "green" if endstatus != "diagnosis_complete_windows_fix_pending" else "yellow"

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": "PI-RS-ASUS-PHYSICAL-DIAG-003",
        "title": "Gabriel – ROG Strix G513QM",
        "machine": {
            "bound": bool(b.get("ok")),
            "profile": b.get("profile") or "asus_rog_gabriel",
            "fingerprint_consistent": bool(b.get("ok")),
            "tone": "green" if b.get("ok") else "red",
        },
        "bios": {
            "installed": bios_d.get("installed") or "G513QM.331",
            "available": bios_d.get("official_available") or "G513QM.335",
            "status": bios_d.get("status") or "update_available",
            "flash_performed": False,
            "tone": "yellow",
        },
        "nvme_a": _nvme_slot(nvme_a, "NVMe A"),
        "nvme_b": _nvme_slot(nvme_b, "NVMe B"),
        "windows": {
            "panther_found": panther,
            "rollback_found": win.get("rollback_found"),
            "setup_phase": win.get("setup_phase") or "UNKNOWN",
            "error_code": win.get("error_code") or "",
            "likely_cause": win.get("likely_cause") or "unknown",
            "confidence": win.get("confidence") or "low",
            "next_step": win.get("next_step") or "controlled_hardware_discovery_on_gabriel",
            "tone": win_tone,
        },
        "endstatus": endstatus,
        "overall_tone": overall,
        "msi_storage_map_shown": False,
        "write_authorization": False,
    }


def build_rescue_installation_readiness(
    *,
    msi_bios: Mapping[str, Any] | None = None,
    asus_bios: Mapping[str, Any] | None = None,
    windows_diag: Mapping[str, Any] | None = None,
    windows_install: Mapping[str, Any] | None = None,
    linux_install: Mapping[str, Any] | None = None,
    endstatus: str = "implemented_pending_physical_diagnosis",
) -> dict[str, Any]:
    msi = dict(msi_bios or {})
    asus = dict(asus_bios or {})
    win_d = dict(windows_diag or {})
    win_i = dict(windows_install or {})
    lin = dict(linux_install or {})

    # Plans are never green.
    if win_i.get("status") == "plan_ready":
        win_i_tone = "yellow"
    else:
        win_i_tone = _tone(win_i.get("status"))

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": "PI-RS-ASUS-WIN11-LINUX-001",
        "endstatus": endstatus,
        "firmware": {
            "msi": {
                "installed": msi.get("installed_version"),
                "status": msi.get("status") or "gray",
                "tone": _tone(msi.get("status")),
                "update_recommended": msi.get("status") == "update_available",
                "flashed": False,
            },
            "asus": {
                "installed": asus.get("installed_version"),
                "status": asus.get("status") or "gray",
                "tone": _tone(asus.get("status")),
                "update_recommended": asus.get("status") == "update_available",
                "flashed": False,
            },
        },
        "asus_windows": {
            "identity": win_d.get("machine"),
            "nvme": win_d.get("windows_target"),
            "health": win_d.get("nvme_health"),
            "evidence": win_d.get("evidence_status"),
            "media": win_d.get("media_status"),
            "preflight": win_d.get("preflight_status"),
            "likely_cause": win_d.get("likely_cause"),
            "install_status": win_i.get("status") or "gray",
            "tone": _tone(win_d.get("preflight_status") or win_d.get("evidence_status")),
        },
        "asus_linux": {
            "nvme": lin.get("linux_target"),
            "distro": lin.get("distro"),
            "iso": lin.get("iso_status"),
            "plan": lin.get("plan_status"),
            "gate": lin.get("gate_status"),
            "install_status": lin.get("status") or "gray",
            "boot_check": lin.get("boot_check"),
            "tone": "yellow" if lin.get("status") == "plan_ready" else _tone(lin.get("status")),
        },
        "safety": {
            "automatic_bios_flash": False,
            "windows_before_linux": True,
            "device_path_not_trusted": True,
            "serial_redacted_in_dcc": True,
        },
        "next_action": _next_action(endstatus),
    }


def _next_action(endstatus: str) -> str:
    mapping = {
        "implemented_pending_physical_diagnosis": "Run MSI BIOS audit and ASUS read-only diagnosis",
        "diagnosis_complete_windows_fix_pending": "Authorize Windows install after cause review",
        "ready_for_windows_install": "Operator Windows 11 install on confirmed NVMe",
        "ready_for_controlled_windows_retest_with_log_collection": "Bind NVMe roles and run Stage A under BIOS 331",
        "ready_for_windows_retest_bios331": "Operator Stage A Windows 11 retest under BIOS G513QM.331",
        "windows_installed_on_bios_331": "Run Windows postcheck; BIOS 335 optional maintenance later",
        "ready_for_bios_335_controlled_update": "Operator ASUS EZ Flash to G513QM.335 then Stage B",
        "bios_335_installed_retest_pending": "Repeat identical Windows retest under BIOS 335",
        "windows_installed_on_bios_335": "Run Windows postcheck before Linux planning",
        "windows_installed_linux_pending": "Select Linux distro and confirm second NVMe",
        "linux_installed_postcheck_pending": "Verify dual-boot and EFI isolation",
        "blocked_linux_nvme_isolation": "Isolate Linux NVMe before Windows Setup",
        "blocked_install_media_corrupt": "Replace official Windows 11 media",
        "blocked_bios_update": "Resolve BIOS 335 update gate blockers",
        "passed": "None",
        "blocked": "Resolve identity/health/media blockers",
        "failed": "Stop and investigate safety failure",
    }
    return mapping.get(endstatus, "Review DCC readiness")


def build_win11_retest_005_dcc(**kwargs: Any) -> dict[str, Any]:
    """Thin wrapper — canonical builder lives in controlled_retest module."""
    return build_win11_retest_dcc(**kwargs)
