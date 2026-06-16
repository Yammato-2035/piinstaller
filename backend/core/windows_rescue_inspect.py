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
    if shell_status in ("path_not_checkable", "not_scanned") and not bitlocker.get("access_allowed"):
        codes.append("WIN-SHELL-003")
    if windows_health.get("user_profile_presence"):
        codes.append("WIN-PROFILE-001")
    if windows_health.get("user_profile_presence") is False and not bitlocker.get("access_allowed"):
        codes.append("WIN-PROFILE-002")

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
        if ack_status == "acknowledged" and hash_match is False:
            ack_status = "hash_mismatch"
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
    if ack in ("hash_mismatch",) or transport.get("hash_match") is False:
        return {"ampel": "red", "classification": "telemetry_hash_mismatch"}
    if ack in ("sent_no_ack", "sending", "sent_unconfirmed", "queued_local", "not_created", "failed"):
        return {"ampel": "yellow", "classification": "telemetry_not_delivered"}
    return {"ampel": "yellow", "classification": "telemetry_not_delivered"}


OPERATOR_PLAN_REL = "docs/evidence/windows-rescue/operator_windows_readonly_plan_latest.json"
REPORT_LATEST_REL = "docs/evidence/windows-rescue/windows_inspect_report_latest.json"
ENVELOPE_LATEST_REL = "docs/evidence/windows-rescue/windows_rescue_telemetry_envelope_latest.json"
STATUS_LATEST_REL = "docs/evidence/windows-rescue/operator_hardware_run_status_latest.json"
ACK_LATEST_REL = "docs/evidence/windows-rescue/operator_telemetry_ack_latest.json"


def _repartition_gate() -> dict[str, Any]:
    return {
        "blocked": True,
        "reasons": [
            "bitlocker_clarified",
            "important_data_inventoried",
            "cloud_backup_plan_confirmed",
            "real_backup_successful",
            "telemetry_acknowledged",
            "hash_match_true",
            "operator_approval",
            "target_nvme_partition_plan_reviewed",
            "windows11_pro_stable_install_medium_available",
            "linux_mint_target_version_set",
            "bootmanager_strategy_reviewed",
        ],
        "blocked_until": {
            "bitlocker_clarified": False,
            "important_data_inventoried": False,
            "cloud_backup_plan_confirmed": False,
            "real_backup_successful": False,
            "telemetry_acknowledged": False,
            "hash_match": False,
            "operator_confirmation": False,
            "target_disk_plan_reviewed": False,
            "windows11_pro_stable_medium_available": False,
            "linux_mint_target_version_set": False,
            "bootmanager_strategy_reviewed": False,
        },
        "bootmanager_notes": [
            "Windows updates must not permanently break boot chain.",
            "Strategy must be Windows-update-resilient.",
            "Document UEFI boot order before any future write track.",
            "No bootloader write in this track.",
        ],
    }


def _dualboot_gate() -> dict[str, Any]:
    return {
        "planning_only": True,
        "target": "Windows 11 Pro stable + Linux Mint (~1 TB)",
        "bootloader_strategy": "planning_only",
        "windows_update_resilience_required": True,
        "linux_mint_size_hint_bytes": 1099511627776,
        "blockers": ["WIN-DUALBOOT-001", "WIN-REPARTITION-001", "WIN-BOOTLOADER-001"],
    }


def normalize_telemetry_status(raw: str | None) -> str:
    val = str(raw or "not_created").strip().lower()
    aliases = {"queued": "queued_local", "queue": "queued_local"}
    val = aliases.get(val, val)
    allowed = {
        "not_created",
        "queued_local",
        "sent_no_ack",
        "acknowledged",
        "hash_mismatch",
        "failed",
        "sending",
        "sent_unconfirmed",
    }
    return val if val in allowed else "not_created"


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_awaiting_operator_status() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "updated_at": utc_now_iso(),
        "status": "awaiting_operator_hardware_run",
        "operator_mode": "B",
        "real_laptop_data_present": False,
        "sample_used_as_evidence": False,
        "bitlocker_status_known": False,
        "windows_file_access_allowed": False,
        "telemetry_ack_present": False,
        "hash_match": False,
        "completion_ampel": "yellow",
        "completion_classification": "awaiting_operator_hardware_run",
        "next_prompt_id": "WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN_PENDING",
    }


def ingest_operator_hardware_run(
    repo_root: Path | str,
    *,
    plan_path: Path | str | None = None,
    ack_path: Path | str | None = None,
    write_outputs: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root)
    plan_file = Path(plan_path) if plan_path else root / OPERATOR_PLAN_REL

    if not plan_file.is_file():
        status = build_awaiting_operator_status()
        if write_outputs:
            _write_json(root / STATUS_LATEST_REL, status)
        return {"ingest_status": "awaiting_operator_hardware_run", "operator_status": status}

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    hw_plan = plan.get("hardware") if isinstance(plan.get("hardware"), dict) else {}
    overrides = {
        "cpu_vendor": hw_plan.get("cpu_vendor"),
        "cpu_model": hw_plan.get("cpu_model"),
        "gpu_vendor": hw_plan.get("gpu_vendor"),
        "gpu_model": hw_plan.get("gpu_model"),
        "memory_bytes": hw_plan.get("memory_bytes"),
        "edition": "Windows 11 Pro",
        "insider_or_beta_hint": "suspected_insider_channel",
    }
    run_id = f"win-operator-{utc_now_iso().replace(':', '').replace('-', '')[:15]}"
    report = build_inspect_report_from_plan(
        plan,
        run_id=run_id,
        hardware_overrides=overrides,
        source="operator_hardware_readonly_run",
        data_classification="operator_hardware_readonly_run",
    )

    ack_payload: dict[str, Any] | None = None
    ack_file = Path(ack_path) if ack_path else root / ACK_LATEST_REL
    if ack_file.is_file():
        ack_payload = json.loads(ack_file.read_text(encoding="utf-8"))

    ack_status = "not_created"
    server_ack_id = None
    server_hash = None
    if ack_payload:
        ack_status = normalize_telemetry_status(str(ack_payload.get("status") or "acknowledged"))
        server_ack_id = ack_payload.get("ack_id") or ack_payload.get("server_ack_id")
        server_hash = ack_payload.get("payload_hash_sha256")

    envelope = build_telemetry_envelope(
        report,
        run_id=run_id,
        device_session_id=f"devsess-{run_id[-12:]}",
        ack_status=ack_status,
        server_ack_id=str(server_ack_id) if server_ack_id else None,
        server_confirmed_hash_sha256=str(server_hash) if server_hash else None,
    )
    completion = evaluate_completion(report, envelope)

    tel = report.setdefault("telemetry", {})
    if isinstance(tel, dict):
        tel["ack_status"] = envelope["telemetry_transport"]["status"]
        tel["hash_match"] = envelope["telemetry_transport"].get("hash_match")
        tel["server_ack_id"] = envelope["telemetry_transport"].get("server_ack_id")

    bitlocker_known = str(report.get("bitlocker", {}).get("status") or "unknown") != "unknown"
    next_prompt = "WINDOWS11_RESCUE_TELEMETRY_ACK_REQUIRED"
    if completion["ampel"] == "green":
        next_prompt = "WINDOWS11_RESCUE_CLOUD_BACKUP_SELECTION_DRY_RUN"
    elif not bitlocker_known:
        next_prompt = "WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN_PENDING"

    operator_status = {
        "schema_version": 1,
        "updated_at": utc_now_iso(),
        "status": "operator_hardware_run_ingested",
        "operator_mode": "A",
        "real_laptop_data_present": True,
        "sample_used_as_evidence": False,
        "bitlocker_status_known": bitlocker_known,
        "windows_file_access_allowed": report.get("safety", {}).get("bitlocker_access_allowed") is True,
        "telemetry_ack_present": ack_status == "acknowledged" and bool(server_ack_id),
        "hash_match": envelope["telemetry_transport"].get("hash_match") is True,
        "completion_ampel": completion["ampel"],
        "completion_classification": completion["classification"],
        "next_prompt_id": next_prompt,
        "run_id": run_id,
    }

    result = {
        "ingest_status": "ok",
        "report": report,
        "telemetry_envelope": envelope,
        "completion": completion,
        "operator_status": operator_status,
    }
    try:
        from core.rescue_telemetry_client import build_rescue_stick_telemetry_client_preview
        from core.telemetry_client_contract import TelemetryOptInState

        result["telemetry_client_preview"] = build_rescue_stick_telemetry_client_preview(
            report,
            run_id=run_id,
            opt_in_state=TelemetryOptInState.DISABLED,
        )
    except Exception:  # noqa: BLE001
        result["telemetry_client_preview"] = {"status": "error", "validation_errors": ["preview_build_failed"]}
    if write_outputs:
        _write_json(root / REPORT_LATEST_REL, report)
        _write_json(root / ENVELOPE_LATEST_REL, envelope)
        _write_json(root / STATUS_LATEST_REL, operator_status)
    return result


def build_inspect_report_from_plan(
    plan: dict[str, Any],
    *,
    run_id: str = "win-inspect-plan-stub",
    hardware_overrides: dict[str, Any] | None = None,
    source: str = "setuphelfer_rescue_inspect",
    data_classification: str = "plan_stub",
) -> dict[str, Any]:
    """Build a structured inspect report from a read-only mount plan (no mounts executed)."""
    hw = hardware_overrides or {}
    hw_plan = plan.get("hardware") if isinstance(plan.get("hardware"), dict) else {}
    bitlocker_raw = plan.get("bitlocker") if isinstance(plan.get("bitlocker"), dict) else {}
    bitlocker_eval = evaluate_bitlocker_access(bitlocker_raw)
    access_allowed = bitlocker_eval["access_allowed"]
    nvme_devices = plan.get("nvme_devices") if isinstance(plan.get("nvme_devices"), list) else []
    if not nvme_devices and isinstance(hw_plan.get("nvme_devices"), list):
        nvme_devices = hw_plan["nvme_devices"]

    health_hints = plan.get("windows_health_hints") if isinstance(plan.get("windows_health_hints"), dict) else {}
    windows_health: dict[str, Any] = {
        "explorer_shell_status": health_hints.get("explorer_shell_status")
        or ("unknown_blocked" if not access_allowed else "not_scanned"),
        "winlogon_shell_hint": health_hints.get("winlogon_shell_hint")
        if access_allowed
        else None,
        "user_profile_presence": health_hints.get("user_profile_presence")
        if access_allowed
        else False,
        "registry_available": health_hints.get("registry_available") if access_allowed else False,
        "eventlog_available": health_hints.get("eventlog_available") if access_allowed else False,
        "boot_config_hint": "plan_only",
        "shell_registry_path": "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\\Shell",
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
        "source": source,
        "data_classification": data_classification,
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
            "cpu_vendor": hw.get("cpu_vendor") or hw_plan.get("cpu_vendor") or "AMD",
            "cpu_model": hw.get("cpu_model") or hw_plan.get("cpu_model") or "Ryzen",
            "gpu_vendor": hw.get("gpu_vendor") or hw_plan.get("gpu_vendor") or "NVIDIA",
            "gpu_model": hw.get("gpu_model") or hw_plan.get("gpu_model"),
            "memory_bytes": hw.get("memory_bytes") or hw_plan.get("memory_bytes"),
            "nvme_devices": nvme_devices,
            "rescue_hostname": hw_plan.get("rescue_hostname"),
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
        "repartition_readiness": _repartition_gate(),
        "dualboot_readiness": _dualboot_gate(),
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
        report = json.loads(sample_path.read_text(encoding="utf-8"))
        report.setdefault("data_classification", "sample_only_not_operator_evidence")
        report.setdefault("source", "setuphelfer_rescue_inspect_sample")
        return report
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
    "ACK_LATEST_REL",
    "ENVELOPE_LATEST_REL",
    "OPERATOR_PLAN_REL",
    "REPORT_LATEST_REL",
    "STATUS_LATEST_REL",
    "build_awaiting_operator_status",
    "build_inspect_report_from_plan",
    "build_inspect_report_from_sample",
    "build_telemetry_envelope",
    "classify_diagnostic_codes",
    "evaluate_bitlocker_access",
    "evaluate_completion",
    "ingest_operator_hardware_run",
    "load_operator_readonly_sample",
    "normalize_telemetry_status",
    "privacy_guard_blocks",
    "sha256_canonical_json",
]
