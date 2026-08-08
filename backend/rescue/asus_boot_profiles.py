"""
ASUS ROG G513QM rescue boot profiles — one primary variable per attempt.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 7.

Does not permanently overwrite the default GRUB profile. Profiles are selected
explicitly via kernel cmdline flags / menu entries.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

PROFILE_SCHEMA_VERSION = 1

# NVIDIA + Nouveau off while AMD path is under test (except profiles that allow open hybrid diag).
_NVIDIA_BLACKLIST = "modprobe.blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm,nouveau"

ASUS_PROFILES: dict[str, dict[str, Any]] = {
    "ASUS-00": {
        "title": "ASUS-00 FORENSIC TUI SAFE",
        "hypothesis": "Safe text-mode boot with full baseline capture and telemetry spool",
        "expected_outcome": "tui_ready_baseline_complete_telemetry_queued_or_sent",
        "cmdline_extra": (
            "setuphelfer_start_assistant=1 "
            "setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
            "setuphelfer_collect_diagnostics=1 nomodeset "
            "setuphelfer_asus_profile=ASUS-00 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": False,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-RECOVERY",
        "allowed_deviations": ["network_offline_queued_telemetry"],
        "primary_variable": "safe_tui_baseline",
    },
    "ASUS-01": {
        "title": "ASUS-01 AMD DISCOVERY",
        "hypothesis": "Removing nomodeset/amdgpu.modeset=0 enables AMD DRM path without forcing GUI",
        "expected_outcome": "amdgpu_bound_drm_cards_present_gui_not_forced",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=text setuphelfer_kiosk=0 pci=noaer {_NVIDIA_BLACKLIST} "
            "setuphelfer_asus_profile=ASUS-01 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": False,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-00",
        "allowed_deviations": ["amdgpu_probe_limited"],
        "primary_variable": "amd_modeset_enabled",
        "forbids_cmdline": ["nomodeset", "amdgpu.modeset=0"],
    },
    "ASUS-02": {
        "title": "ASUS-02 AMD GUI",
        "hypothesis": "Internal display works via AMD DRM when ASUS-01 DRM gate is green",
        "expected_outcome": "drm_ready_and_rescue_ui_or_controlled_tui_fallback",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 pci=noaer "
            f"{_NVIDIA_BLACKLIST} setuphelfer_asus_profile=ASUS-02 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": True,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 600,
        "fallback_profile": "ASUS-00",
        "allowed_deviations": ["gui_timeout_falls_back_to_tui"],
        "primary_variable": "gui_on_amd_path",
        "forbids_cmdline": ["nomodeset", "amdgpu.modeset=0"],
        "requires_prior_profiles": ["ASUS-01"],
    },
    "ASUS-03": {
        "title": "ASUS-03 HYBRID OPEN DRIVER DIAGNOSTIC",
        "hypothesis": "AMD remains primary; NVIDIA open/nouveau only if module present and unblocked",
        "expected_outcome": "hybrid_inventory_without_proprietary_nvidia",
        "cmdline_extra": (
            "setuphelfer_start_assistant=1 "
            "setuphelfer_mode=text setuphelfer_kiosk=0 pci=noaer "
            "setuphelfer_asus_profile=ASUS-03 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": False,
        "allows_proprietary_nvidia": False,
        "allows_nouveau_if_safe": True,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-00",
        "allowed_deviations": ["nouveau_left_unloaded_when_unsafe"],
        "primary_variable": "open_hybrid_inventory",
        "requires_prior_profiles": ["ASUS-01"],
    },
    "ASUS-04": {
        "title": "ASUS-04 NVIDIA MODULE COMPATIBILITY",
        "hypothesis": "Diagnose proprietary NVIDIA module/kernel compatibility without installing",
        "expected_outcome": "nvidia_compat_report_no_install",
        "cmdline_extra": (
            "setuphelfer_start_assistant=1 "
            "setuphelfer_mode=text setuphelfer_kiosk=0 "
            "setuphelfer_asus_profile=ASUS-04 setuphelfer_nvidia_diag_only=1 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": False,
        "allows_proprietary_nvidia": False,
        "install_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-00",
        "allowed_deviations": ["module_absent_reported_concretely"],
        "primary_variable": "nvidia_module_compat_probe",
        "requires_prior_profiles": ["ASUS-01", "ASUS-03"],
    },
    "ASUS-05": {
        "title": "ASUS-05 FULL GUI CANDIDATE",
        "hypothesis": "Consistent AMD/NVIDIA findings from ASUS-01..04 allow a GUI candidate boot",
        "expected_outcome": "gui_candidate_or_documented_block",
        "cmdline_extra": (
            "setuphelfer_start_assistant=1 "
            "setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
            "setuphelfer_asus_profile=ASUS-05 "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": True,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 600,
        "fallback_profile": "ASUS-RECOVERY",
        "allowed_deviations": ["gui_blocked_with_concrete_driver_firmware_reasons"],
        "primary_variable": "full_gui_candidate",
        "requires_prior_profiles": ["ASUS-01", "ASUS-02", "ASUS-03", "ASUS-04"],
    },
    "ASUS-RECOVERY": {
        "title": "ASUS-RECOVERY FORCED TUI FALLBACK",
        "hypothesis": "Always-bootable forensic TUI fallback",
        "expected_outcome": "tui_boot_always",
        "cmdline_extra": (
            "setuphelfer_start_assistant=1 "
            "setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1 "
            "setuphelfer_collect_diagnostics=1 nomodeset "
            "setuphelfer_asus_profile=ASUS-RECOVERY "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0"
        ),
        "allows_gui": False,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-RECOVERY",
        "allowed_deviations": [],
        "primary_variable": "forced_tui_recovery",
        "must_remain_bootable": True,
    },
    # PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — TUI first, then forensic X, then controlled GUI.
    "ASUS-TUI-BASELINE": {
        "title": "ASUS-TUI-BASELINE (006 reference)",
        "hypothesis": "Stable text rescue with AMD modeset, no GUI/Chromium/startx autostart",
        "expected_outcome": "asus_tui_baseline_stable",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_tui_baseline=1 "
            f"setuphelfer_gui_watchdog=0 pci=noaer {_NVIDIA_BLACKLIST} "
            "setuphelfer_asus_profile=ASUS-TUI-BASELINE "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
            "setuphelfer_telemetry_opt_in=1 "
            "setuphelfer_auto_hw_baseline=1"
        ),
        "allows_gui": False,
        "allows_startx": False,
        "allows_chromium": False,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "auto_hw_baseline": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-RECOVERY",
        "allowed_deviations": ["network_offline_queued_telemetry"],
        "primary_variable": "tui_baseline_reference_006",
        "forbids_cmdline": ["setuphelfer_mode=gui", "setuphelfer_kiosk=1"],
    },
    # PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 — high-info TUI baseline (no Chromium autostart).
    "ASUS-TUI-BASELINE-HIGHINFO": {
        "title": "ASUS-TUI-BASELINE-HIGHINFO (007 high-info)",
        "hypothesis": (
            "Same stable TUI baseline as ASUS-TUI-BASELINE, plus high-info capture "
            "(setuphelfer_highinfo / isolated Xorg probe); Chromium is NOT auto-started"
        ),
        "expected_outcome": "asus_tui_baseline_highinfo_stable_probe_isolated",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_tui_baseline=1 "
            f"setuphelfer_highinfo=1 setuphelfer_xorg_probe=1 "
            f"setuphelfer_gui_watchdog=0 pci=noaer {_NVIDIA_BLACKLIST} "
            "setuphelfer_asus_profile=ASUS-TUI-BASELINE-HIGHINFO "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
            "setuphelfer_telemetry_opt_in=1 "
            "setuphelfer_auto_hw_baseline=1"
        ),
        "allows_gui": False,
        "allows_startx": False,
        "allows_chromium": False,
        "allows_proprietary_nvidia": False,
        "xorg_probe_isolated": True,
        "chromium_autostart": False,
        "telemetry_required": True,
        "capture_required": True,
        "auto_hw_baseline": True,
        "highinfo": True,
        "timeout_sec": 900,
        "fallback_profile": "ASUS-TUI-BASELINE",
        "allowed_deviations": [
            "network_offline_queued_telemetry",
            "xorg_probe_skipped_or_classified_fail",
        ],
        "primary_variable": "tui_baseline_highinfo_007",
        "notes": (
            "Chromium is NOT auto-started. Xorg probe (setuphelfer_xorg_probe=1) is "
            "controlled/isolated and must not launch a browser or GUI kiosk."
        ),
        "forbids_cmdline": ["setuphelfer_mode=gui", "setuphelfer_kiosk=1"],
    },
    "ASUS-XORG-FORENSIC": {
        "title": "ASUS-XORG-FORENSIC (006 startx only)",
        "hypothesis": "Controlled startx→Xorg→X-socket without Chromium",
        "expected_outcome": "xorg_display_ready_or_classified_fail",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_xorg_forensic=1 "
            f"setuphelfer_gui_watchdog=0 pci=noaer {_NVIDIA_BLACKLIST} "
            "setuphelfer_asus_profile=ASUS-XORG-FORENSIC "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
            "setuphelfer_telemetry_opt_in=1"
        ),
        "allows_gui": False,
        "allows_startx": True,
        "allows_chromium": False,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 600,
        "fallback_profile": "ASUS-TUI-BASELINE",
        "allowed_deviations": ["xorg_failed_with_forensic_evidence"],
        "primary_variable": "startx_xorg_socket_only",
        "forbids_cmdline": ["nomodeset", "amdgpu.modeset=0", "setuphelfer_mode=gui"],
        "requires_prior_profiles": ["ASUS-TUI-BASELINE"],
    },
    "ASUS-GUI-CONTROLLED": {
        "title": "ASUS-GUI-CONTROLLED (006 after xorg_display_ready)",
        "hypothesis": "Chromium only after Xorg display ready + ports/backend ready",
        "expected_outcome": "gui_browser_once_or_blocked_with_gate",
        "cmdline_extra": (
            f"setuphelfer_start_assistant=1 "
            f"setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_controlled=1 "
            f"setuphelfer_gui_watchdog=1 pci=noaer {_NVIDIA_BLACKLIST} "
            "setuphelfer_asus_profile=ASUS-GUI-CONTROLLED "
            "setuphelfer_msi_lab_auto=0 setuphelfer_auto_discovery=0 "
            "setuphelfer_telemetry_opt_in=1"
        ),
        "allows_gui": True,
        "allows_startx": True,
        "allows_chromium": True,
        "allows_proprietary_nvidia": False,
        "telemetry_required": True,
        "capture_required": True,
        "timeout_sec": 600,
        "fallback_profile": "ASUS-TUI-BASELINE",
        "allowed_deviations": ["gui_timeout_falls_back_to_tui"],
        "primary_variable": "controlled_chromium_after_xorg",
        "forbids_cmdline": ["nomodeset", "amdgpu.modeset=0"],
        "requires_prior_profiles": ["ASUS-TUI-BASELINE", "ASUS-XORG-FORENSIC"],
    },
}


_FLAG = re.compile(r"(?:^|\s)setuphelfer_asus_profile=([A-Z0-9-]+)(?:\s|$)")


def list_asus_profiles() -> list[str]:
    return list(ASUS_PROFILES.keys())


def get_asus_profile(profile_id: str) -> dict[str, Any]:
    if profile_id not in ASUS_PROFILES:
        raise KeyError(f"unknown_asus_profile:{profile_id}")
    body = dict(ASUS_PROFILES[profile_id])
    body["profile_id"] = profile_id
    body["schema_version"] = PROFILE_SCHEMA_VERSION
    return body


def resolve_asus_profile_from_cmdline(cmdline: str = "") -> dict[str, Any]:
    match = _FLAG.search(cmdline or "")
    profile_id = match.group(1) if match else "ASUS-00"
    if profile_id not in ASUS_PROFILES:
        profile_id = "ASUS-RECOVERY"
    profile = get_asus_profile(profile_id)
    profile["active"] = bool(match) or profile_id == "ASUS-00"
    profile["cmdline_observed"] = cmdline or ""
    violations = validate_cmdline_against_profile(cmdline or "", profile_id)
    profile["cmdline_violations"] = violations
    return profile


def validate_cmdline_against_profile(cmdline: str, profile_id: str) -> list[str]:
    profile = get_asus_profile(profile_id)
    violations: list[str] = []
    for forbidden in profile.get("forbids_cmdline") or []:
        if re.search(rf"(?:^|\s){re.escape(forbidden)}(?:\s|$)", cmdline):
            violations.append(f"forbidden_present:{forbidden}")
    if profile_id == "ASUS-00" and "nomodeset" not in cmdline and "setuphelfer_asus_profile=ASUS-00" in cmdline:
        # Soft warning only — menu append should include nomodeset.
        violations.append("asus00_missing_nomodeset")
    return violations


def profile_gate_allows(
    profile_id: str,
    *,
    completed_profiles: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """completed_profiles maps profile_id -> result status (e.g. proceed/failed)."""
    profile = get_asus_profile(profile_id)
    done = dict(completed_profiles or {})
    missing = [p for p in profile.get("requires_prior_profiles") or [] if done.get(p) not in {"passed", "proceed", "ok"}]
    return {
        "profile_id": profile_id,
        "allowed": not missing,
        "missing_prior_profiles": missing,
        "reason": "prior_profiles_incomplete" if missing else "ok",
    }


def build_menu_append(profile_id: str, base_live: str) -> str:
    profile = get_asus_profile(profile_id)
    return f"{base_live} {profile['cmdline_extra']}".strip()
