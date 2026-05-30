"""Read-only lokaler Collector für den Development Agent."""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from devserver_agent.models import build_dev_node, build_dev_report, new_report_id, resolve_node_identity, utc_now_iso

FORBIDDEN_TOKENS = frozenset({
    "dd", "mkfs", "mount", "umount", "parted", "sfdisk", "sgdisk", "wipefs",
    "sudo", "apt", "rm", "chmod", "chown", "tee", "scp",
})

_SYSTEMCTL_WRITE_RE = re.compile(r"\bsystemctl\s+(start|stop|restart|enable|disable|mask|unmask)\b", re.I)

HARDWARE_COMMANDS = [
    "uname -a",
    "lscpu",
    "free -b",
    "hostnamectl",
    "cat /etc/os-release 2>/dev/null || true",
]

STORAGE_COMMANDS = [
    "lsblk -J -O",
    "findmnt -J",
    "blkid -o export 2>/dev/null || true",
]

BOOT_COMMANDS = [
    "test -d /sys/firmware/efi && echo UEFI || echo BIOS",
    "mokutil --sb-state 2>/dev/null || true",
    "efibootmgr -v 2>/dev/null || true",
    "ls /boot 2>/dev/null || true",
    "ls /boot/efi/EFI 2>/dev/null || true",
]

RESCUE_RUNTIME_COMMANDS = [
    "systemctl is-system-running 2>/dev/null || true",
    "ps -p 1 -o comm= 2>/dev/null || true",
    "ip -j addr 2>/dev/null || true",
    "date -Is",
]

MAX_OUTPUT_BYTES = 64 * 1024
COMMAND_TIMEOUT_SEC = 15


class CollectorError(Exception):
    pass


def _validate_command(cmd: str) -> None:
    lowered = cmd.lower()
    if _SYSTEMCTL_WRITE_RE.search(cmd):
        raise CollectorError("forbidden_token:systemctl_write")
    stripped = re.sub(r"2>/dev/null", "", cmd, flags=re.IGNORECASE)
    stripped = re.sub(r"2>&1", "", stripped)
    if ">" in stripped or ">>" in stripped:
        raise CollectorError("write_redirection_blocked")
    if "| tee" in lowered:
        raise CollectorError("write_redirection_blocked")
    for token in FORBIDDEN_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            raise CollectorError(f"forbidden_token:{token}")


def _truncate(text: str, limit: int = MAX_OUTPUT_BYTES) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _run_command(cmd: str) -> dict[str, Any]:
    _validate_command(cmd)
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SEC,
            check=False,
        )
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": _truncate(proc.stdout or ""),
            "stderr": _truncate(proc.stderr or ""),
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "exit_code": -1, "stdout": "", "stderr": "timeout"}
    except OSError as exc:
        return {"command": cmd, "exit_code": -1, "stdout": "", "stderr": str(exc)}


def _run_commands(commands: list[str]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    results: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    for cmd in commands:
        try:
            result = _run_command(cmd)
            results.append(result)
            if result.get("exit_code") not in (0, None):
                warnings.append(f"command_nonzero:{cmd}")
        except CollectorError as exc:
            errors.append(str(exc))
    return results, warnings, errors


def collect_hardware_inventory() -> dict[str, Any]:
    results, warnings, errors = _run_commands(HARDWARE_COMMANDS)
    payload: dict[str, Any] = {
        "collected_at": utc_now_iso(),
        "commands": results,
        "cpu": {},
        "memory": {},
    }
    for r in results:
        if r.get("command", "").startswith("lscpu"):
            payload["cpu"]["raw"] = r.get("stdout", "")
        if r.get("command", "").startswith("free"):
            payload["memory"]["raw"] = r.get("stdout", "")
    payload["warnings"] = warnings
    payload["errors"] = errors
    return payload


def collect_storage_topology() -> dict[str, Any]:
    results, warnings, errors = _run_commands(STORAGE_COMMANDS)
    payload: dict[str, Any] = {"collected_at": utc_now_iso(), "commands": results}
    for r in results:
        if "lsblk" in str(r.get("command")):
            try:
                payload["lsblk"] = json.loads(r.get("stdout") or "{}")
            except json.JSONDecodeError:
                payload["lsblk_raw"] = r.get("stdout", "")
                warnings.append("lsblk_json_parse_failed")
    payload["warnings"] = warnings
    payload["errors"] = errors
    return payload


def collect_boot_profile() -> dict[str, Any]:
    results, warnings, errors = _run_commands(BOOT_COMMANDS)
    firmware = "unknown"
    for r in results:
        out = (r.get("stdout") or "").strip()
        if out in ("UEFI", "BIOS"):
            firmware = out
    return {
        "collected_at": utc_now_iso(),
        "firmware_mode": firmware,
        "commands": results,
        "warnings": warnings,
        "errors": errors,
    }


def collect_rescue_runtime() -> dict[str, Any]:
    results, warnings, errors = _run_commands(RESCUE_RUNTIME_COMMANDS)
    return {
        "collected_at": utc_now_iso(),
        "commands": results,
        "warnings": warnings,
        "errors": errors,
    }


def build_dev_report_from_collection(
    *,
    node_id: str,
    mode: str,
    collect_hardware: bool = True,
    collect_storage: bool = True,
    collect_boot: bool = True,
    setuphelfer_version: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload: dict[str, Any] = {"agent_status": "collected", "collected_at": utc_now_iso()}
    all_warnings: list[str] = []
    all_errors: list[str] = []

    if collect_hardware:
        hw = collect_hardware_inventory()
        payload["hardware"] = hw
        all_warnings.extend(hw.get("warnings") or [])
        all_errors.extend(hw.get("errors") or [])

    if collect_storage:
        st = collect_storage_topology()
        payload["storage"] = st
        all_warnings.extend(st.get("warnings") or [])
        all_errors.extend(st.get("errors") or [])

    if collect_boot:
        boot = collect_boot_profile()
        payload["boot"] = boot
        all_warnings.extend(boot.get("warnings") or [])
        all_errors.extend(boot.get("errors") or [])

    rescue = collect_rescue_runtime()
    payload["rescue_runtime"] = rescue
    all_warnings.extend(rescue.get("warnings") or [])
    all_errors.extend(rescue.get("errors") or [])

    report_type = "rescue" if mode == "local_lab" else "inventory"
    report = build_dev_report(
        report_id=new_report_id(),
        node_id=node_id,
        report_type=report_type,
        mode=mode,
        payload=payload,
        setuphelfer_version=setuphelfer_version,
        warnings=all_warnings,
        errors=all_errors,
    )
    return report, payload


def build_dev_node_from_config(
    *,
    node_id: str,
    display_name: str,
    mode: str,
) -> dict[str, Any]:
    nid, dname = resolve_node_identity(node_id, display_name)
    return build_dev_node(node_id=nid, display_name=dname, mode=mode)
