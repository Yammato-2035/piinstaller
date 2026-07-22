"""DCC / readiness aggregation for firmware + Win11 + Linux second NVMe workflow."""

from __future__ import annotations

from typing import Any, Mapping

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
        "windows_installed_linux_pending": "Select Linux distro and confirm second NVMe",
        "linux_installed_postcheck_pending": "Verify dual-boot and EFI isolation",
        "passed": "None",
        "blocked": "Resolve identity/health/media blockers",
        "failed": "Stop and investigate safety failure",
    }
    return mapping.get(endstatus, "Review DCC readiness")
