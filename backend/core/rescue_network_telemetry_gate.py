"""Rescue network/telemetry gate fields and blocker derivation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.rescue_telemetry_ingest import build_health_payload, load_rescue_telemetry_ingest_config
from core.rescue_telemetry_lan_proxy import build_compact_telemetry_lan_proxy_status
from core.rescue_telemetry_tasks import build_compact_task_pull_status


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_gate_file() -> dict[str, Any]:
    path = _repo_root() / "docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _ingest_ack_present() -> bool:
    cfg = load_rescue_telemetry_ingest_config()
    ack_dir = cfg.ack_dir
    if ack_dir.is_dir():
        for path in ack_dir.glob("*.json"):
            if path.is_file():
                return True
    status_path = _repo_root() / "docs/evidence/runtime-results/rescue/rescue_telemetry_ingest_runtime_status.json"
    if status_path.is_file():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            return bool(data.get("last_ack_id"))
        except (OSError, json.JSONDecodeError):
            pass
    health = build_health_payload()
    return bool(health.get("last_ack_id"))


def derive_network_telemetry_gate(gate: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = gate or load_gate_file()
    proxy = build_compact_telemetry_lan_proxy_status()
    tasks = build_compact_task_pull_status()
    booted = gate.get("target_laptop_booted_from_stick") is True
    live_stable = gate.get("target_live_media_runtime_stable") is True
    link = gate.get("target_network_link_established") is True
    health_reached = gate.get("target_telemetry_health_reached") is True
    ingest_ack = gate.get("target_telemetry_ingest_ack") is True or _ingest_ack_present()
    onboarding_available = gate.get("target_network_onboarding_available")
    if onboarding_available is None:
        onboarding_available = True
    blockers: list[str] = []
    if not onboarding_available:
        blockers.append("RESCUE_NETWORK_ONBOARDING_REQUIRED")
    if booted and not link:
        blockers.append("RESCUE_WIFI_SCAN_NOT_TRIGGERED")
        blockers.append("RESCUE_WIFI_PASSWORD_PROMPT_MISSING")
    if link and not health_reached:
        blockers.append("RESCUE_TARGET_TELEMETRY_HEALTH_NOT_REACHED")
    if health_reached and not ingest_ack:
        blockers.append("RESCUE_TARGET_TELEMETRY_INGEST_ACK_MISSING")
    if gate.get("target_live_media_runtime_stable") is False:
        blockers.append("RESCUE_TARGET_LIVE_MEDIA_SQUASHFS_IO_ERROR")
    if not tasks.get("controlled_task_pull_available"):
        blockers.append("RESCUE_CONTROLLED_TASK_PULL_NOT_AVAILABLE")
    if not proxy.get("lan_health_ok"):
        blockers.append("RESCUE_MSI_TELEMETRY_PROXY_NOT_READY")
    windows_inspect = (
        gate.get("iso_uefi_validated") is True
        and gate.get("usb_stick_written") is True
        and gate.get("usb_write_sha256_verified") is True
        and booted
        and live_stable
        and link
        and health_reached
        and ingest_ack
    )
    return {
        "target_laptop_booted_from_stick": booted,
        "target_live_media_runtime_stable": live_stable,
        "target_network_onboarding_available": onboarding_available,
        "target_network_link_established": link,
        "target_network_ip": gate.get("target_network_ip"),
        "target_default_route_present": gate.get("target_default_route_present") is True,
        "target_telemetry_health_reached": health_reached,
        "target_telemetry_ingest_ack": ingest_ack,
        "developer_lan_telemetry_proxy_ready": proxy.get("running") and proxy.get("lan_health_ok"),
        "controlled_task_pull_available": tasks.get("controlled_task_pull_available"),
        "windows_inspect_executable": windows_inspect,
        "blockers": blockers,
        "last_error_code": gate.get("msi_network_onboarding_last_error"),
    }


def build_compact_network_telemetry_status() -> dict[str, Any]:
    gate = load_gate_file()
    derived = derive_network_telemetry_gate(gate)
    proxy = build_compact_telemetry_lan_proxy_status()
    tasks = build_compact_task_pull_status()
    health = build_health_payload()
    tone = "red"
    if derived.get("target_telemetry_ingest_ack"):
        tone = "green"
    elif derived.get("target_telemetry_health_reached"):
        tone = "yellow"
    elif derived.get("developer_lan_telemetry_proxy_ready"):
        tone = "yellow"
    return {
        "status_tone": tone,
        "proxy_ready": bool(proxy.get("running") and proxy.get("lan_health_ok")),
        "proxy_health_url": proxy.get("health_url"),
        "msi_ip": derived.get("target_network_ip"),
        "wlan_connected": derived.get("target_network_link_established"),
        "telemetry_health_reached": derived.get("target_telemetry_health_reached"),
        "telemetry_ingest_ack": derived.get("target_telemetry_ingest_ack"),
        "controlled_task_pull_available": tasks.get("controlled_task_pull_available"),
        "last_task_id": tasks.get("last_task_id"),
        "last_task_result": tasks.get("last_task_result"),
        "last_error_code": derived.get("last_error_code") or health.get("last_error_code"),
        "windows_inspect_executable": derived.get("windows_inspect_executable"),
        "blockers": derived.get("blockers") or [],
        "next_step": (
            "MSI: setuphelfer-rescue-network-onboarding; setuphelfer-rescue-telemetry-push"
            if derived.get("developer_lan_telemetry_proxy_ready")
            else "Developer: LAN-Proxy starten"
        ),
        "secrets_exposed": False,
    }
