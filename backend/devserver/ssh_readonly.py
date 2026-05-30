"""Read-only SSH-Diagnostik mit Allowlist-Profilen."""

from __future__ import annotations

import re
import shlex
import subprocess
from typing import Any, Callable

from devserver.models import default_dev_report, new_id, utc_now_iso

FORBIDDEN_TOKENS = frozenset({
    "dd", "mkfs", "mount", "umount", "parted", "sfdisk", "sgdisk", "wipefs",
    "sudo", "apt", "rm", "chmod", "chown", "systemctl", "tee", "scp", "curl", "wget",
})

ALLOWED_PROFILES: dict[str, list[str]] = {
    "ssh_check": [
        "uname -a",
        "id",
        "hostnamectl --static 2>/dev/null || hostname",
        "date -Is",
    ],
    "collect_inventory": [
        "uname -a",
        "lscpu",
        "free -b",
        "hostnamectl",
        "cat /etc/os-release 2>/dev/null || true",
    ],
    "collect_storage": [
        "lsblk -J -O",
        "findmnt -J",
        "blkid -o export 2>/dev/null || true",
    ],
    "collect_boot": [
        "test -d /sys/firmware/efi && echo UEFI || echo BIOS",
        "mokutil --sb-state 2>/dev/null || true",
        "efibootmgr -v 2>/dev/null || true",
        "ls /boot 2>/dev/null || true",
        "ls /boot/efi/EFI 2>/dev/null || true",
    ],
}

PROFILE_TO_ACTION_TYPE = {
    "ssh_check": "ssh_check",
    "collect_inventory": "collect_inventory",
    "collect_storage": "collect_storage",
    "collect_boot": "collect_boot",
}

PROFILE_TO_REPORT_TYPE = {
    "ssh_check": "ssh_probe",
    "collect_inventory": "inventory",
    "collect_storage": "storage",
    "collect_boot": "boot",
}

MAX_OUTPUT_BYTES = 64 * 1024
SSH_TIMEOUT_SEC = 30

SshRunner = Callable[[list[str], int], dict[str, Any]]


class SshReadonlyError(Exception):
    pass


def validate_command_profile(profile_name: str) -> bool:
    return profile_name in ALLOWED_PROFILES


def _validate_single_command(cmd: str) -> None:
    lowered = cmd.lower()
    stripped = re.sub(r"2>/dev/null", "", cmd, flags=re.IGNORECASE)
    stripped = re.sub(r"2>&1", "", stripped)
    if ">" in stripped or ">>" in stripped:
        raise SshReadonlyError("write_redirection_blocked")
    if "| tee" in lowered:
        raise SshReadonlyError("write_redirection_blocked")
    for token in FORBIDDEN_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            raise SshReadonlyError(f"forbidden_token:{token}")


def build_readonly_command_list(profile_name: str) -> list[str]:
    if profile_name not in ALLOWED_PROFILES:
        raise SshReadonlyError("unknown_profile")
    commands = list(ALLOWED_PROFILES[profile_name])
    for cmd in commands:
        _validate_single_command(cmd)
    return commands


def _default_ssh_runner(argv: list[str], timeout_sec: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": -1,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": "ssh_timeout",
        }
    except OSError as exc:
        return {"exit_code": -1, "stdout": "", "stderr": str(exc)}


def _truncate(text: str, limit: int = MAX_OUTPUT_BYTES) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _build_ssh_argv(node: dict[str, Any], remote_script: str) -> list[str]:
    ssh_cfg = node.get("ssh") or {}
    host = str(ssh_cfg.get("host") or "").strip()
    username = str(ssh_cfg.get("username") or "").strip()
    port = int(ssh_cfg.get("port") or 22)
    if not host or not username:
        raise SshReadonlyError("ssh_not_configured")
    target = f"{username}@{host}"
    return [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=10",
        "-p", str(port),
        target,
        remote_script,
    ]


def run_ssh_profile(
    node: dict[str, Any],
    profile_name: str,
    *,
    runner: SshRunner | None = None,
) -> dict[str, Any]:
    commands = build_readonly_command_list(profile_name)
    ssh_cfg = node.get("ssh") or {}
    if not ssh_cfg.get("enabled"):
        return {
            "ok": False,
            "blocked": True,
            "reason": "ssh_disabled_on_node",
            "commands": commands,
            "stdout": "",
            "stderr": "",
            "exit_code": None,
        }
    host = str(ssh_cfg.get("host") or "").strip()
    username = str(ssh_cfg.get("username") or "").strip()
    if not host or not username:
        return {
            "ok": False,
            "blocked": True,
            "reason": "ssh_not_configured",
            "commands": commands,
            "stdout": "",
            "stderr": "",
            "exit_code": None,
        }
    remote_script = "; ".join(commands)
    _validate_single_command(remote_script)
    argv = _build_ssh_argv(node, remote_script)
    run = runner or _default_ssh_runner
    result = run(argv, SSH_TIMEOUT_SEC)
    exit_code = result.get("exit_code")
    stdout = _truncate(str(result.get("stdout") or ""))
    stderr = _truncate(str(result.get("stderr") or ""))
    ok = exit_code == 0
    return {
        "ok": ok,
        "blocked": False,
        "reason": None if ok else "ssh_command_failed",
        "commands": commands,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
    }


def parse_ssh_result_to_report(
    node: dict[str, Any],
    profile_name: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    report_type = PROFILE_TO_REPORT_TYPE.get(profile_name, "ssh_probe")
    payload: dict[str, Any] = {
        "profile": profile_name,
        "commands": result.get("commands") or [],
        "stdout_excerpt": result.get("stdout") or "",
        "stderr_excerpt": result.get("stderr") or "",
        "exit_code": result.get("exit_code"),
    }
    if profile_name == "collect_inventory" and result.get("stdout"):
        payload["raw_stdout"] = result.get("stdout")
    if profile_name == "collect_storage" and result.get("stdout"):
        payload["raw_stdout"] = result.get("stdout")
    if profile_name == "collect_boot" and result.get("stdout"):
        payload["raw_stdout"] = result.get("stdout")

    report = default_dev_report(
        report_id=new_id("report"),
        node_id=str(node.get("node_id") or ""),
        report_type=report_type,
        lab_mode=str(node.get("lab_mode") or "local_lab"),
        payload=payload,
        redaction_status="raw_lab",
    )
    if not result.get("ok"):
        report["warnings"].append(str(result.get("reason") or "ssh_failed"))
    return report
