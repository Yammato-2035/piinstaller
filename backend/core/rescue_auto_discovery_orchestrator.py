"""Rescue auto-discovery orchestrator — read-only MSI exploration (001D7/001D7B)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from core.rescue_discovery_run_control import consume_discovery_run_control, load_discovery_run_control
from core.rescue_component_heartbeat import write_component_heartbeat
from core.rescue_evidence_completeness import validate_session_evidence
from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_physical_e2e_msi_evidence_complete import (
    msi_evidence_complete_ok,
    read_msi_evidence_complete,
)
from core.rescue_privacy_redaction import build_privacy_summary
from core.rescue_run_mode import resolve_run_mode
from core.rescue_session_state import (
    append_journal,
    heartbeat,
    init_session_state,
    mark_terminal,
    session_evidence_dir,
    session_journal_path,
    session_state_path,
    set_phase,
)
from core.rescue_setup_logs_persistence import ensure_setup_logs_rw
from core.rescue_storage_discovery import discover_rescue_storage

MSI_EVIDENCE_WAIT_SEC = 900
def _state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))

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


def _wait_msi_evidence_complete(setup_logs_base: Path | None, *, max_wait_sec: int = MSI_EVIDENCE_WAIT_SEC) -> bool:
    set_phase("msi_evidence_waiting", warning="Warte auf MSI-Evidence-Marker…")
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        heartbeat(warning="MSI-Evidence-Marker-Warten")
        if setup_logs_base and msi_evidence_complete_ok(setup_logs_base):
            return True
        if (_state_dir() / "auto-msi-evidence.done").is_file() and setup_logs_base:
            data = read_msi_evidence_complete(setup_logs_base)
            if data and data.get("status") == "passed" and data.get("late_gate_completed"):
                return True
        # Re-detect SETUP_LOGS if it appeared later.
        if setup_logs_base is None:
            detected = find_setup_logs_mount()
            if detected and msi_evidence_complete_ok(detected):
                return True
        time.sleep(2)
    return False


def _persist_session_start(session_dir: Path, state: dict[str, Any], extra: dict[str, Any]) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    _write_artifact(session_dir, "00-session.json", {**state, **extra})
    _write_artifact(session_dir, "state.json", state)
    # Guarantee journal exists beside session evidence (runtime journal already appended).
    journal_src = session_journal_path()
    journal_dst = session_dir / "journal.jsonl"
    if journal_src.is_file():
        journal_dst.write_text(journal_src.read_text(encoding="utf-8"), encoding="utf-8")
    elif not journal_dst.is_file():
        journal_dst.write_text(
            json.dumps({"event": "session_created", "session_id": state.get("session_id")}, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
    append_journal({"event": "discovery_session_persisted", "session_dir": str(session_dir)})


def run_auto_discovery(*, allow_destructive: bool = False) -> dict[str, Any]:
    if allow_destructive:
        raise ValueError("auto_discovery_destructive_forbidden")

    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "auto-discovery.started").write_text("1\n", encoding="utf-8")
    write_component_heartbeat("discovery", state="starting")

    payload_version = rescue_payload_version()
    mode_info = resolve_run_mode()
    run_mode = str(mode_info.get("run_mode") or "auto_discovery_only")
    if not mode_info.get("ok"):
        state = init_session_state(
            payload_version=payload_version,
            source="physical_msi",
            run_mode="blocked",
        )
        mark_terminal(result="blocked", evidence_complete=False, shutdown_safe=True)
        return {
            "status": "blocked_run_mode_conflict",
            "session_id": state["session_id"],
            "run_mode": None,
        }

    state = init_session_state(
        payload_version=payload_version,
        source="physical_msi",
        run_mode=run_mode,
    )
    heartbeat(module="session_created")
    set_phase("discovery_starting", warning="Automatische Systemerkundung startet")
    set_phase("setup_logs_waiting")
    logs = ensure_setup_logs_rw()
    setup_logs_base = Path(str(logs.get("mount_point") or "")) if logs.get("mount_point") else None
    if not setup_logs_base:
        setup_logs_base = find_setup_logs_mount()

    review_setup_logs = False
    if logs.get("writable"):
        set_phase("setup_logs_ready")
    else:
        review_setup_logs = True
        set_phase("setup_logs_ready", warning="review_required_setup_logs_unavailable")

    # Persist start proof immediately (runtime + SETUP_LOGS / fallback).
    session_dir = session_evidence_dir(setup_logs_base, str(state["session_id"]))
    _persist_session_start(
        session_dir,
        state,
        {
            "setup_logs": logs,
            "allow_destructive": False,
            "run_mode": run_mode,
            "runtime_state_path": str(session_state_path()),
        },
    )
    heartbeat(module="00-session")

    if not _wait_msi_evidence_complete(setup_logs_base):
        mark_terminal(result="failed", evidence_complete=False, shutdown_safe=True)
        if setup_logs_base:
            consume_discovery_run_control(
                setup_logs_base,
                consumed_by_session_id=str(state["session_id"]),
                terminal_status="failed_msi_evidence_marker_timeout",
            )
        return {
            "status": "failed_msi_evidence_marker_timeout",
            "session_id": state["session_id"],
            "session_dir": str(session_dir),
            "setup_logs": logs,
        }

    set_phase("discovery_starting", warning="MSI-Evidence abgeschlossen")
    heartbeat(module="msi-evidence-complete")

    machine = _collect_machine(session_dir, state)
    set_phase("firmware_collecting")
    heartbeat(module="firmware")
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
    discovery_summary["run_mode"] = run_mode
    _write_artifact(session_dir, "16-discovery-summary.json", discovery_summary)

    gate = validate_session_evidence(
        session_dir,
        expected_session_id=str(state["session_id"]),
        expected_boot_id=str(state["boot_id"]),
    )
    if review_setup_logs and gate.get("status") == "complete":
        gate = {**gate, "status": "review_required", "code": "review_required_setup_logs_unavailable"}
    _write_artifact(session_dir, "16-discovery-summary.json", {**discovery_summary, "completeness_gate": gate})

    set_phase("evidence_syncing")
    heartbeat(module="evidence_sync")

    result = gate["status"]
    if result == "complete":
        mark_terminal(result="passed", evidence_complete=True, shutdown_safe=True)
        status = "rescue_auto_discovery_evidence_complete"
        terminal_status = "passed"
    elif result == "review_required":
        mark_terminal(result="review_required", evidence_complete=True, shutdown_safe=True)
        status = "rescue_auto_discovery_review_required"
        terminal_status = "review_required"
    else:
        mark_terminal(result="failed", evidence_complete=False, shutdown_safe=True)
        status = "failed_rescue_auto_discovery"
        terminal_status = "failed"

    control_base = setup_logs_base or find_setup_logs_mount()
    if control_base and load_discovery_run_control(control_base):
        consume_discovery_run_control(
            control_base,
            consumed_by_session_id=str(state["session_id"]),
            terminal_status=terminal_status,
        )

    set_phase("shutdown_pending")
    heartbeat(module="shutdown_pending")
    write_component_heartbeat("discovery", state="terminal")
    return {
        "status": status,
        "session_id": state["session_id"],
        "session_dir": str(session_dir),
        "completeness_gate": gate,
        "setup_logs": logs,
        "run_mode": run_mode,
        "terminal": True,
        "shutdown_safe": True,
        "evidence_complete": result in {"complete", "review_required"},
        "session_created": True,
    }


def main() -> dict[str, Any]:
    """Outer exception boundary for the runner (001D7C)."""
    from core.rescue_discovery_observability import (
        boot_id,
        classify_exception,
        exception_summary,
        persist_orchestrator_exit,
        persist_service_result,
    )
    from core.rescue_discovery_boot_completion import harvest_late_journal
    from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount as _find_logs

    started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    try:
        result = run_auto_discovery(allow_destructive=False)
        persist_orchestrator_exit(
            {
                "started": True,
                "started_at": started_at,
                "exit_code": 0,
                "session_created": bool(result.get("session_created") or result.get("session_id")),
                "terminal_state_written": bool(result.get("terminal")),
                "status": result.get("status") or "",
            }
        )
        persist_service_result(
            {
                "exit_code": 0,
                "status": result.get("status") or "",
                "run_control_consumed": True,
                "session_id": result.get("session_id"),
            }
        )
        return result
    except BaseException as exc:  # noqa: BLE001 — intentional outer boundary
        status = classify_exception(exc)
        summary = exception_summary(exc)
        persist_orchestrator_exit(
            {
                "started": True,
                "started_at": started_at,
                "exit_code": 1,
                "exception_type": type(exc).__name__,
                "exception_summary": summary,
                "session_created": False,
                "terminal_state_written": False,
                "status": status,
            }
        )
        logs = _find_logs()
        if logs:
            try:
                consume_discovery_run_control(
                    logs,
                    consumed_by_boot_id=boot_id(),
                    terminal_status=status,
                    failure_stage="orchestrator_exception",
                )
            except OSError:
                pass
        persist_service_result(
            {
                "exit_code": 1,
                "status": status,
                "run_control_consumed": bool(logs),
                "failure_stage": "orchestrator_exception",
            }
        )
        try:
            harvest_late_journal(setup_logs_base=logs)
        except OSError:
            pass
        write_component_heartbeat("discovery", state="failed")
        raise


if __name__ == "__main__":
    main()

