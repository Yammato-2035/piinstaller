"""Windows rescue inspect read-only stub — no mounts, no NTFS writes."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MVP_ACTION_FLAGS = {
    "write_action_allowed": False,
    "repair_action_allowed": False,
    "partition_action_allowed": False,
}

_FORBIDDEN_TELEMETRY_KEYS = (
    "password",
    "cookie",
    "token",
    "private_key",
    "ssh_key",
    "file_content",
    "document_content",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_canonical_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evaluate_bitlocker_access(bitlocker: dict[str, Any]) -> dict[str, Any]:
    status = str(bitlocker.get("status") or "unknown").lower()
    confidence = str(bitlocker.get("confidence") or "low")
    access_allowed = status in ("not_detected", "unlocked")
    blocking_reason: str | None = None
    if status == "unknown":
        blocking_reason = "WIN-BITLOCKER-UNKNOWN"
    elif status == "locked":
        blocking_reason = "WIN-BITLOCKER-LOCKED"
    elif status == "suspended":
        blocking_reason = "WIN-BITLOCKER-006"
    return {
        "status": status,
        "confidence": confidence,
        "access_allowed": access_allowed,
        "blocking_reason": blocking_reason,
    }


def classify_diagnostic_codes(report: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    hardware = report.get("hardware") if isinstance(report.get("hardware"), dict) else {}
    storage = report.get("storage") if isinstance(report.get("storage"), dict) else {}
    bitlocker = report.get("bitlocker") if isinstance(report.get("bitlocker"), dict) else {}
    windows_health = report.get("windows_health") if isinstance(report.get("windows_health"), dict) else {}
    telemetry = report.get("telemetry") if isinstance(report.get("telemetry"), dict) else {}
    repartition = report.get("repartition_readiness") if isinstance(report.get("repartition_readiness"), dict) else {}
    dualboot = report.get("dualboot_readiness") if isinstance(report.get("dualboot_readiness"), dict) else {}

    if not hardware.get("cpu_vendor") or not hardware.get("gpu_vendor"):
        codes.append("WIN-HW-001")
    nvme = hardware.get("nvme_devices")
    if isinstance(nvme, list) and len(nvme) >= 2:
        codes.append("WIN-STORAGE-001")
        codes.append("WIN-STORAGE-003")
    if storage.get("windows_candidates"):
        codes.append("WIN-STORAGE-002")

    bl = evaluate_bitlocker_access(bitlocker)
    if bl["blocking_reason"] == "WIN-BITLOCKER-UNKNOWN":
        codes.append("WIN-BITLOCKER-UNKNOWN")
    elif bl["blocking_reason"] == "WIN-BITLOCKER-LOCKED":
        codes.append("WIN-BITLOCKER-LOCKED")

    shell_status = str(windows_health.get("explorer_shell_status") or "")
    if shell_status in ("missing", "not_configured", "unknown_blocked"):
        codes.append("WIN-SHELL-001")
    if windows_health.get("registry_available") is False:
        codes.append("WIN-SHELL-002")
    if windows_health.get("user_profile_presence"):
        codes.append("WIN-PROFILE-001")

    backup = report.get("backup_selection") if isinstance(report.get("backup_selection"), dict) else {}
    if backup.get("dry_run_only") is True:
        codes.append("WIN-BACKUP-001")

    if telemetry.get("server_ack_required"):
        codes.append("WIN-TELEMETRY-001")
    if telemetry.get("hash_match") is False:
        codes.append("WIN-TELEMETRY-002")
    if repartition.get("blocked"):
        codes.append("WIN-REPARTITION-001")
    if dualboot.get("planning_only"):
        if "WIN-DUALBOOT-001" not in codes:
            codes.append("WIN-DUALBOOT-001")
    if dualboot.get("windows_update_resilience_required"):
        codes.append("WIN-BOOTLOADER-001")

    return list(dict.fromkeys(codes))


def privacy_guard_blocks(payload: dict[str, Any]) -> tuple[bool, str | None]:
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for key in _FORBIDDEN_TELEMETRY_KEYS:
        if f'"{key}"' in blob:
            return True, "TELEMETRY-PRIVACY-001"
    if payload.get("contains_personal_data") is True and payload.get("operator_consent_state") != "granted":
        return True, "TELEMETRY-CONSENT-001"
    return False, None


def build_telemetry_envelope(
    report: dict[str, Any],
    *,
    run_id: str,
    device_session_id: str,
    ack_status: str = "not_created",
    server_ack_id: str | None = None,
    server_confirmed_hash_sha256: str | None = None,
) -> dict[str, Any]:
    report_hash = sha256_canonical_json(report)
    hardware = report.get("hardware") if isinstance(report.get("hardware"), dict) else {}
    bitlocker = report.get("bitlocker") if isinstance(report.get("bitlocker"), dict) else {}
    diagnostics = report.get("diagnostics") if isinstance(report.get("diagnostics"), dict) else {}
    backup = report.get("backup_selection") if isinstance(report.get("backup_selection"), dict) else {}
    dualboot = report.get("dualboot_readiness") if isinstance(report.get("dualboot_readiness"), dict) else {}

    hash_match: bool | None = None
    if server_confirmed_hash_sha256 is not None:
        hash_match = server_confirmed_hash_sha256 == report_hash
    privacy_blocked, privacy_error = privacy_guard_blocks(
        {
            "contains_personal_data": False,
            "operator_consent_state": "not_required_for_diagnostic_metadata",
        }
    )

    envelope: dict[str, Any] = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "device_session_id": device_session_id,
        "created_at": utc_now_iso(),
        "source": "rescue_stick",
        "payload_kind": "windows_rescue_inspect",
        "payload_hash_sha256": report_hash,
        "payload_size_bytes": len(json.dumps(report, ensure_ascii=False).encode("utf-8")),
        "privacy_level": "diagnostic_metadata",
        "contains_personal_data": False,
        "operator_consent_state": "not_required_for_diagnostic_metadata",
        "system": {
            "windows_detected": bool(
                (report.get("storage") or {}).get("windows_candidates")
                if isinstance(report.get("storage"), dict)
                else False
            ),
            "windows_version": report.get("host", {}).get("edition") if isinstance(report.get("host"), dict) else None,
            "windows_channel": report.get("host", {}).get("insider_or_beta_hint") if isinstance(report.get("host"), dict) else "unknown",
            "bitlocker_status": bitlocker.get("status"),
            "device_encryption_status": "unknown",
        },
        "hardware": {
            "cpu_vendor": hardware.get("cpu_vendor"),
            "gpu_vendor": hardware.get("gpu_vendor"),
            "nvme_count": len(hardware.get("nvme_devices") or []) if isinstance(hardware.get("nvme_devices"), list) else None,
            "memory_bytes": hardware.get("memory_bytes"),
        },
        "diagnostics": {
            "codes": diagnostics.get("codes") or classify_diagnostic_codes(report),
            "severity": diagnostics.get("severity") or "unknown",
            "recommended_actions": diagnostics.get("recommended_actions") or [],
        },
        "backup": {
            "selection_created": bool(backup.get("selected_paths")),
            "backup_verified": backup.get("backup_verified") is True,
            "cloud_target_configured": False,
            "manifest_hash": backup.get("manifest_hash"),
        },
        "dualboot": {
            "planning_only": dualboot.get("planning_only", True),
            "repartition_blocked_until_backup_verified": True,
            "windows_boot_manager_fallback": True,
        },
        "telemetry_transport": {
            "status": ack_status,
            "endpoint_configured": False,
            "server_ack_id": server_ack_id,
            "server_ack_at": None,
            "payload_hash_sha256": report_hash,
            "server_confirmed_hash_sha256": server_confirmed_hash_sha256,
            "retry_count": 0,
            "last_error": None,
            "hash_match": hash_match,
            "privacy_guard_blocked": privacy_blocked,
            "privacy_guard_error": privacy_error,
        },
    }

    green = (
        ack_status == "acknowledged"
        and bool(server_ack_id)
        and hash_match
        and not privacy_blocked
    )
    envelope["completion"] = {
        "ampel": "green" if green else ("red" if privacy_blocked or ack_status == "failed_final" else "yellow"),
        "classification": "inspect_and_telemetry_acknowledged" if green else "telemetry_not_delivered",
    }
    return envelope


def evaluate_completion(report: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    transport = envelope.get("telemetry_transport") if isinstance(envelope.get("telemetry_transport"), dict) else {}
    privacy_blocked = transport.get("privacy_guard_blocked") is True
    ack = str(transport.get("status") or "")
    ack_id = transport.get("server_ack_id")
    hash_match = transport.get("hash_match") is True
    if privacy_blocked:
        return {"ampel": "red", "classification": "privacy_guard_blocked"}
    if ack == "acknowledged" and ack_id and hash_match:
        return {"ampel": "green", "classification": "inspect_and_telemetry_acknowledged"}
    if transport.get("hash_match") is False:
        return {"ampel": "red", "classification": "telemetry_hash_mismatch"}
    return {"ampel": "yellow", "classification": "telemetry_not_delivered"}


def build_inspect_report_from_plan(
    plan: dict[str, Any],
    *,
    run_id: str = "win-inspect-plan-stub",
    hardware_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a structured inspect report from a read-only mount plan (no mounts executed)."""
    hw = hardware_overrides or {}
    bitlocker_raw = plan.get("bitlocker") if isinstance(plan.get("bitlocker"), dict) else {}
    bitlocker_eval = evaluate_bitlocker_access(bitlocker_raw)
    access_allowed = bitlocker_eval["access_allowed"]
    nvme_devices = plan.get("nvme_devices") if isinstance(plan.get("nvme_devices"), list) else []

    windows_health: dict[str, Any] = {
        "explorer_shell_status": "unknown_blocked" if not access_allowed else "not_scanned",
        "winlogon_shell_hint": None if not access_allowed else "explorer.exe_expected",
        "user_profile_presence": False if not access_allowed else None,
        "registry_available": False if not access_allowed else None,
        "eventlog_available": False if not access_allowed else None,
        "boot_config_hint": "plan_only",
    }

    backup_selection: dict[str, Any] = {
        "dry_run_only": True,
        "selected_paths": [],
        "candidate_user_dirs": [] if not access_allowed else ["Users/*/Documents", "Users/*/Pictures"],
        "excluded_paths": [
            "AppData/Local/Google/Chrome/User Data",
            "System Volume Information",
            "pagefile.sys",
            "hiberfil.sys",
        ],
        "cloud_policy": "dry_run_no_credentials",
        "backup_verified": False,
        "manifest_hash": None,
    }

    report: dict[str, Any] = {
        "schema_version": 2,
        "run_id": run_id,
        "generated_at": utc_now_iso(),
        "source": "setuphelfer_rescue_inspect",
        "safety": {
            "mode": "read_only",
            "write_actions_allowed": False,
            "cloud_upload_allowed": False,
            "bitlocker_access_allowed": access_allowed,
        },
        "host": {
            "detected_os_family": "windows",
            "edition": hw.get("edition", "Windows 11 Pro"),
            "build": hw.get("build"),
            "insider_or_beta_hint": hw.get("insider_or_beta_hint", "unknown"),
            "computer_name": None,
        },
        "hardware": {
            "cpu_vendor": hw.get("cpu_vendor", "AMD"),
            "cpu_model": hw.get("cpu_model", "Ryzen"),
            "gpu_vendor": hw.get("gpu_vendor", "NVIDIA"),
            "gpu_model": hw.get("gpu_model"),
            "memory_bytes": hw.get("memory_bytes"),
            "nvme_devices": nvme_devices,
            "target_profile": plan.get("hardware_hints", {}).get("target_profile")
            if isinstance(plan.get("hardware_hints"), dict)
            else "2x2TB_NVMe_AMD_Ryzen_NVIDIA",
        },
        "storage": {
            "disks": plan.get("blockdevices") or [],
            "partitions": plan.get("partitions") or [],
            "filesystem_hints": [p.get("fstype") for p in (plan.get("partitions") or []) if isinstance(p, dict)],
            "efi_candidates": plan.get("efi_candidates") or [],
            "windows_candidates": plan.get("windows_candidates") or [],
            "linux_candidates": plan.get("linux_candidates") or [],
        },
        "bitlocker": {
            **bitlocker_raw,
            **bitlocker_eval,
        },
        "windows_health": windows_health,
        "backup_selection": backup_selection,
        "telemetry": {
            "required": True,
            "local_report_hash": None,
            "server_ack_required": True,
            "ack_status": "not_created",
            "hash_match": None,
        },
        "repartition_readiness": {
            "blocked": True,
            "reasons": [
                "backup_manifest_verified",
                "telemetry_acknowledged",
                "hash_match",
                "operator_confirmation",
                "target_disk_plan_reviewed",
            ],
            "blocked_until": {
                "backup_manifest_verified": False,
                "telemetry_acknowledged": False,
                "hash_match": False,
                "operator_confirmation": False,
                "target_disk_plan_reviewed": False,
            },
        },
        "dualboot_readiness": {
            "planning_only": True,
            "target": "Windows 11 Pro stable + Linux Mint",
            "bootloader_strategy": "planning_only",
            "windows_update_resilience_required": True,
            "blockers": ["WIN-DUALBOOT-001", "WIN-REPARTITION-001"],
        },
        "readonly_mount_plan": plan.get("readonly_mount_plan") or [],
        "blocked_reasons": plan.get("blocked_reasons") or [],
        "required_operator_actions": plan.get("required_operator_actions") or [],
    }
    report["telemetry"]["local_report_hash"] = sha256_canonical_json(report)
    report["diagnostics"] = {
        "codes": classify_diagnostic_codes(report),
        "severity": "warning" if not access_allowed else "info",
        "recommended_actions": report.get("required_operator_actions") or [],
    }
    return report


def load_operator_readonly_sample(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    sample_path = root / "docs/evidence/windows-rescue/windows_inspect_operator_readonly_sample.json"
    if sample_path.is_file():
        return json.loads(sample_path.read_text(encoding="utf-8"))
    return build_inspect_report_from_plan(
        {
            "bitlocker": {"status": "unknown", "confidence": "low"},
            "nvme_devices": [{"name": "nvme0n1"}, {"name": "nvme1n1"}],
            "partitions": [],
            "windows_candidates": [],
            "hardware_hints": {"target_profile": "2x2TB_NVMe_AMD_Ryzen_NVIDIA", "dual_nvme_detected": True},
            "blocked_reasons": ["bitlocker_unknown_blocks_file_access"],
            "required_operator_actions": ["VERIFY_BITLOCKER_BEFORE_READONLY_MOUNT"],
        },
        run_id="win-inspect-fallback-sample",
    )


def build_inspect_report_from_sample(repo_root: Path | str | None = None) -> dict[str, Any]:
    report = load_operator_readonly_sample(repo_root)
    if not report.get("telemetry", {}).get("local_report_hash"):
        tel = report.setdefault("telemetry", {})
        if isinstance(tel, dict):
            tel["local_report_hash"] = sha256_canonical_json(report)
    if not report.get("diagnostics"):
        report["diagnostics"] = {
            "codes": classify_diagnostic_codes(report),
            "severity": "warning",
            "recommended_actions": report.get("required_operator_actions") or [],
        }
    return report


__all__ = [
    "build_inspect_report_from_plan",
    "build_inspect_report_from_sample",
    "build_telemetry_envelope",
    "classify_diagnostic_codes",
    "evaluate_bitlocker_access",
    "evaluate_completion",
    "load_operator_readonly_sample",
    "privacy_guard_blocks",
    "sha256_canonical_json",
]
