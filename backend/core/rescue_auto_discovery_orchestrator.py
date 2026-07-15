"""Rescue auto-discovery orchestrator — read-only MSI exploration (001D7)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from core.rescue_evidence_completeness import validate_session_evidence
from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_payload_version import rescue_payload_version
from core.rescue_privacy_redaction import build_privacy_summary
from core.rescue_session_state import (
    heartbeat,
    init_session_state,
    mark_terminal,
    session_evidence_dir,
    set_phase,
)
from core.rescue_setup_logs_persistence import ensure_setup_logs_rw
from core.rescue_storage_discovery import discover_rescue_storage

CollectorFn = Callable[[Path, dict[str, Any]], dict[str, Any]]

REQUIRED_MODULE_NAMES = (
    "machine",
    "cpu_memory",
    "pci_usb",
    "storage",
    "smart",
    "kernel",
    "network",
    "services",
    "payload",
)


def _utc_meta(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "setuphelfer.rescue.discovery-artifact.v1",
        "session_id": state.get("session_id"),
        "boot_id": state.get("boot_id"),
        "payload_version": state.get("payload_version"),
        "created_at": state.get("updated_at"),
        "collector_status": "ok",
        "warnings": [],
        "errors": [],
    }


def _write_artifact(session_dir: Path, name: str, payload: dict[str, Any]) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    fd = os.open(str(session_dir), os.O_DIRECTORY)
    os.fsync(fd)
    os.close(fd)
    return path


def _run(cmd: list[str], *, timeout: int = 30) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def _collect_machine(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("machine_identity_collecting")
    payload = _utc_meta(state)
    for key, cmd in (
        ("vendor", ["dmidecode", "-s", "system-manufacturer"]),
        ("product_name", ["dmidecode", "-s", "system-product-name"]),
        ("product_version", ["dmidecode", "-s", "system-version"]),
        ("board_vendor", ["dmidecode", "-s", "baseboard-manufacturer"]),
        ("board_name", ["dmidecode", "-s", "baseboard-product-name"]),
        ("bios_vendor", ["dmidecode", "-s", "bios-vendor"]),
        ("bios_version", ["dmidecode", "-s", "bios-version"]),
    ):
        rc, out = _run(cmd)
        payload[key] = out if rc == 0 else ""
    payload["architecture"] = platform.machine()
    payload["kernel"] = platform.release()
    payload["vendor_class"] = "msi" if "micro-star" in str(payload.get("vendor", "")).lower() else "unknown"
    payload["model_family"] = "GE63 Raider" if "ge63" in str(payload.get("product_name", "")).lower() else "unknown"
    _write_artifact(session_dir, "01-machine.json", payload)
    heartbeat(module="01-machine")
    return payload


def _collect_cpu_memory(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("cpu_memory_collecting")
    payload = _utc_meta(state)
    rc, lscpu = _run(["lscpu", "-J"])
    payload["lscpu"] = json.loads(lscpu) if rc == 0 and lscpu else {}
    rc, mem = _run(["free", "-b"])
    payload["memory_raw"] = mem if rc == 0 else ""
    _write_artifact(session_dir, "03-cpu-memory.json", payload)
    heartbeat(module="03-cpu-memory")
    return payload


def _collect_pci_usb(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("pci_collecting")
    pci = _utc_meta(state)
    rc, out = _run(["lspci", "-nn"])
    pci["lspci_redacted"] = out if rc == 0 else ""
    _write_artifact(session_dir, "04-pci.json", pci)
    set_phase("usb_collecting")
    usb = _utc_meta(state)
    rc, out = _run(["lsusb"])
    usb["lsusb_redacted"] = out if rc == 0 else ""
    _write_artifact(session_dir, "05-usb.json", usb)
    heartbeat(module="05-usb")
    return usb


def _wait_usb_devices(max_wait_sec: int = 120) -> None:
    set_phase("storage_waiting", warning="USB-Geräte werden gesucht…")
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        discovery = discover_rescue_storage()
        targets = discovery.get("targets") or []
        if targets:
            break
        heartbeat(warning=f"USB-Wartephase {int(max_wait_sec - max(0, deadline - time.time()))}s")
        subprocess.run(["udevadm", "settle"], capture_output=True, check=False, timeout=30)
        time.sleep(2)


def _collect_storage(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    _wait_usb_devices()
    set_phase("storage_collecting")
    discovery = discover_rescue_storage()
    payload = _utc_meta(state)
    payload["discovery"] = discovery
    _write_artifact(session_dir, "06-storage.json", payload)
    set_phase("partition_collecting")
    partitions = [d for d in discovery.get("classified") or [] if str(d.get("type")) == "part"]
    part_payload = _utc_meta(state)
    part_payload["partitions"] = partitions
    _write_artifact(session_dir, "07-partitions.json", part_payload)
    set_phase("filesystem_collecting")
    fs_payload = _utc_meta(state)
    fs_payload["filesystems"] = [
        {
            "path": p.get("path"),
            "fstype": p.get("fstype"),
            "label": p.get("label"),
            "mountpoint": p.get("mountpoint"),
            "role": p.get("role"),
        }
        for p in partitions
    ]
    _write_artifact(session_dir, "08-filesystems.json", fs_payload)
    heartbeat(module="08-filesystems")
    return payload


def _collect_smart(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("smart_collecting")
    payload = _utc_meta(state)
    payload["devices"] = []
    for disk in discover_rescue_storage().get("classified") or []:
        if str(disk.get("type")) != "disk":
            continue
        path = str(disk.get("path") or "")
        if not path:
            continue
        if "nvme" in path:
            rc, out = _run(["nvme", "smart-log", path])
        else:
            rc, out = _run(["smartctl", "-H", path])
        payload["devices"].append(
            {
                "path": path,
                "smart_status": "ok" if rc == 0 else "unsupported",
                "summary_redacted": out[:500] if out else "",
            }
        )
    _write_artifact(session_dir, "09-smart.json", payload)
    heartbeat(module="09-smart")
    return payload


def _collect_kernel(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("kernel_collecting")
    payload = _utc_meta(state)
    rc, dmesg = _run(["dmesg", "--level=warn,err,crit,alert,emerg"])
    payload["dmesg_redacted"] = dmesg if rc == 0 else ""
    rc, journal = _run(["journalctl", "-b", "-p", "warning", "--no-pager", "-n", "200"])
    payload["journal_warnings_redacted"] = journal if rc == 0 else ""
    payload["findings"] = []
    for token in ("FAT-fs", "I/O error", "reset high-speed USB", "Corrected error"):
        if token.lower() in (dmesg + journal).lower():
            payload["findings"].append({"code": token.replace(" ", "_").upper(), "severity": "warning"})
    _write_artifact(session_dir, "12-kernel-findings.json", payload)
    heartbeat(module="12-kernel-findings")
    return payload


def _collect_network(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("network_hardware_collecting")
    hw = _utc_meta(state)
    rc, out = _run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"])
    hw["nmcli_redacted"] = out if rc == 0 else ""
    _write_artifact(session_dir, "10-network-hardware.json", hw)
    set_phase("lan_collecting")
    conn = build_network_connectivity_v2()
    _write_artifact(session_dir, "11-network-connectivity.json", {**_utc_meta(state), **conn})
    heartbeat(module="11-network-connectivity")
    return conn


def _collect_services(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("services_collecting")
    payload = _utc_meta(state)
    units = (
        "setuphelfer-backend.service",
        "setuphelfer-rescue-tui.service",
        "setuphelfer-rescue-auto-msi-evidence.service",
        "setuphelfer-rescue-auto-physical-e2e.service",
        "setuphelfer-rescue-auto-discovery.service",
        "NetworkManager.service",
    )
    payload["services"] = []
    for unit in units:
        rc, out = _run(["systemctl", "show", unit, "--property=ActiveState,SubState,Result"])
        payload["services"].append({"unit": unit, "show": out if rc == 0 else ""})
    rc, failed = _run(["systemctl", "--failed", "--no-pager"])
    payload["failed_units_raw"] = failed if rc == 0 else ""
    _write_artifact(session_dir, "13-services.json", payload)
    heartbeat(module="13-services")
    return payload


def _collect_payload(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    set_phase("payload_collecting")
    payload = _utc_meta(state)
    expected = rescue_payload_version()
    api_version = ""
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/version", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            api_version = str(data.get("project_version") or data.get("version") or "")
    except (OSError, json.JSONDecodeError, ValueError):
        api_version = ""
    payload["expected_payload_version"] = expected
    payload["api_version"] = api_version
    payload["all_versions_match"] = bool(api_version) and api_version == expected
    if not payload["all_versions_match"]:
        payload["collector_status"] = "review_required"
    _write_artifact(session_dir, "14-payload-version.json", payload)
    heartbeat(module="14-payload-version")
    return payload


def run_auto_discovery(*, allow_destructive: bool = False) -> dict[str, Any]:
    payload_version = rescue_payload_version()
    state = init_session_state(payload_version=payload_version, source="physical_msi")
    set_phase("setup_logs_waiting")
    logs = ensure_setup_logs_rw()
    setup_logs_base = Path(str(logs.get("mount_point") or "")) if logs.get("mount_point") else None
    if logs.get("writable"):
        set_phase("setup_logs_ready")
    else:
        set_phase("setup_logs_ready", warning=str(logs.get("status") or "fallback"))

    session_dir = session_evidence_dir(setup_logs_base, str(state["session_id"]))
    session_payload = {**state, "setup_logs": logs, "allow_destructive": allow_destructive}
    _write_artifact(session_dir, "00-session.json", session_payload)
    _write_artifact(session_dir, "state.json", state)

    machine = _collect_machine(session_dir, state)
    _collect_cpu_memory(session_dir, state)
    _collect_pci_usb(session_dir, state)
    _collect_storage(session_dir, state)
    _collect_smart(session_dir, state)
    _collect_kernel(session_dir, state)
    _collect_network(session_dir, state)
    _collect_services(session_dir, state)
    payload_info = _collect_payload(session_dir, state)

    set_phase("privacy_redaction")
    summary_payload = {
        "machine": machine,
        "storage": discover_rescue_storage(),
        "payload": payload_info,
    }
    privacy = build_privacy_summary(payload=summary_payload)
    privacy.update(_utc_meta(state))
    _write_artifact(session_dir, "15-privacy-summary.json", privacy)

    set_phase("evidence_validation")
    discovery_summary = _utc_meta(state)
    discovery_summary["modules_completed"] = REQUIRED_MODULE_NAMES
    _write_artifact(session_dir, "16-discovery-summary.json", discovery_summary)

    gate = validate_session_evidence(
        session_dir,
        expected_session_id=str(state["session_id"]),
        expected_boot_id=str(state["boot_id"]),
    )
    _write_artifact(session_dir, "16-discovery-summary.json", {**discovery_summary, "completeness_gate": gate})

    result = gate["status"]
    if result == "complete":
        mark_terminal(result="passed", evidence_complete=True, shutdown_safe=True)
        status = "rescue_auto_discovery_evidence_complete"
    elif result == "review_required":
        mark_terminal(result="review_required", evidence_complete=True, shutdown_safe=True)
        status = "rescue_auto_discovery_review_required"
    else:
        mark_terminal(result="failed", evidence_complete=False, shutdown_safe=False)
        status = "failed_rescue_auto_discovery"

    return {
        "status": status,
        "session_id": state["session_id"],
        "session_dir": str(session_dir),
        "completeness_gate": gate,
        "setup_logs": logs,
    }
