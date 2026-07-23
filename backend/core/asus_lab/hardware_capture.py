"""Hardware/firmware capture helpers — wraps collectors; missing tools = warning."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from core.asus_lab.capture_manifest import record_artifact

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_cmd(cmd: Sequence[str], timeout: int = 60) -> dict[str, Any]:
    if not shutil.which(cmd[0]):
        return {
            "ok": False,
            "exit_code": 127,
            "stdout": "",
            "stderr": f"tool_missing:{cmd[0]}",
            "warning": True,
        }
    try:
        proc = subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "exit_code": 124, "stdout": "", "stderr": str(exc)[:500], "warning": True}
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": (proc.stderr or "")[:2000],
        "warning": proc.returncode != 0,
    }


def write_command_artifact(
    run_root: Path,
    *,
    relative_path: str,
    category: str,
    collector: str,
    cmd: Sequence[str],
    timeout: int = 60,
) -> dict[str, Any]:
    started = utc_now()
    result = _run_cmd(cmd, timeout=timeout)
    out = run_root / relative_path
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "command": list(cmd),
        "started_at": started,
        "completed_at": utc_now(),
        **result,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    errors = []
    if result.get("warning"):
        errors.append(str(result.get("stderr") or "command_warning")[:200])
    entry = record_artifact(
        run_root,
        relative_path=relative_path,
        category=category,
        collector=collector,
        started_at=started,
        exit_code=int(result.get("exit_code") or 0),
        errors=errors,
    )
    return {**result, "manifest_entry": entry}


def run_baseline_hardware_capture(run_root: Path) -> dict[str, Any]:
    """Best-effort baseline; never aborts whole run on missing tools."""
    specs = [
        ("system/uname.json", "system", ["uname", "-a"]),
        ("system/cmdline.json", "system", ["cat", "/proc/cmdline"]),
        ("system/lscpu.json", "system", ["lscpu"]),
        ("disks/lsblk.json", "disks", ["lsblk", "-J", "-O"]),
        ("disks/blkid.json", "disks", ["blkid"]),
        ("firmware/efibootmgr.json", "firmware", ["efibootmgr", "-v"]),
        ("network/ip-addr.json", "network", ["ip", "-j", "addr"]),
        ("graphics/lspci.json", "graphics", ["lspci", "-nnk"]),
    ]
    results = []
    for rel, cat, cmd in specs:
        results.append(write_command_artifact(run_root, relative_path=rel, category=cat, collector="baseline", cmd=cmd))
    warnings = sum(1 for r in results if r.get("warning"))
    return {
        "schema_version": SCHEMA_VERSION,
        "collectors": len(results),
        "warnings": warnings,
        "status": "partial" if warnings else "complete",
        "bitlocker_mutation": False,
    }
