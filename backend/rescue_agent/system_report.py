from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from typing import Any

from rescue_agent.nftables_policy import build_nftables_policy_preview

UTC = timezone.utc


def _safe_device_identity(agent_id: str) -> dict[str, Any]:
    return {
        "machine_id_hash": hashlib.sha256(agent_id.encode("utf-8")).hexdigest(),
        "dmi_vendor": "unknown",
        "dmi_product": "unknown",
        "serial_hash": None,
    }


def build_rescue_system_report(
    *,
    agent_id: str,
    session_id: str,
    discovery_result: dict[str, Any],
    e2ee_status: str = "contract_stub",
) -> dict[str, Any]:
    now = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    review_required: list[str] = []
    storage_summary: dict[str, Any] = {"devices": [], "system_disks": [], "external_disks": [], "backup_candidates": []}
    try:
        from core.storage_facade import build_storage_inventory_snapshot

        snapshot = build_storage_inventory_snapshot(mode="rescue")
        rows = snapshot.get("lsblk_rows") if isinstance(snapshot.get("lsblk_rows"), list) else []
        storage_summary["devices"] = rows[:20]
        storage_summary["backup_candidates"] = snapshot.get("backup_target_candidates", [])
        for dev in rows[:20]:
            name = str(dev.get("name") or "")
            tran = str(dev.get("tran") or "")
            if tran == "usb":
                storage_summary["external_disks"].append(name)
            elif name.startswith(("sd", "nvme", "vd")):
                storage_summary["system_disks"].append(name)
    except Exception:
        review_required.append("core_facade_missing_for_rescue_agent")

    try:
        from core.mount_facade import build_mount_inventory_snapshot

        mount_inventory = build_mount_inventory_snapshot(target="/")
        boot_detected = [m.get("target") for m in mount_inventory.get("current_mounts", []) if m.get("target") in ("/boot", "/efi")]
    except Exception:
        mount_inventory = {"status": "review_required"}
        boot_detected = []
        review_required.append("core_facade_missing_for_rescue_agent")

    nft_preview = build_nftables_policy_preview(
        discovery_phase=discovery_result.get("method") in {"mdns", "udp_broadcast"},
        validated_endpoint=discovery_result.get("discovery_status") == "found",
    )
    report = {
        "schema_version": "1.0",
        "created_at": now,
        "agent_id": agent_id,
        "session_id": session_id,
        "hostname": "rescue-live",
        "identity": {
            "agent_kind": "rescue_stick",
            "agent_version": "0.1.0-stub",
            "boot_id": hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16],
            "device_identity": _safe_device_identity(agent_id),
            "privacy": {
                "no_plain_serials": True,
                "no_plain_ip_persistence": True,
                "operator_consent_required": True,
            },
        },
        "os": {
            "live_system": True,
            "base": "debian-live",
            "kernel": platform.release(),
            "architecture": platform.machine() or "x86_64",
        },
        "hardware": {
            "cpu_model": platform.processor() or "unknown",
            "memory_total_bytes": 0,
            "firmware": "unknown",
            "secure_boot": "unknown",
        },
        "network": {
            "interfaces": [],
            "devserver_discovery": discovery_result.get("discovery_status", "not_found"),
            "devserver_endpoint_hash": discovery_result.get("endpoint_hash", ""),
            "site_hint": "",
        },
        "storage": storage_summary,
        "boot": {"boot_mode": "unknown", "efi_partitions": boot_detected, "detected_os": []},
        "safety": {
            "nftables_active": True,
            "nftables_policy_status": nft_preview.get("policy_status"),
            "write_operations_allowed": False,
            "restore_allowed": False,
            "backup_allowed": False,
            "dangerous_actions_locked": True,
        },
        "evidence": {
            "local_log_path": "",
            "report_hash": "",
            "encrypted_transport": e2ee_status in {"stub_ok", "required"},
            "e2ee_status": e2ee_status,
        },
        "review_required": sorted(set(review_required)),
        "mount_inventory_status": mount_inventory.get("status"),
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    report["evidence"]["report_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report

