"""PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — port ownership probes (no blind kill)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

PORT_OWNERSHIP_SCHEMA_VERSION = 1

_DEFAULT_EXPECTED = {
    8000: "setuphelfer-backend",
    8765: "setuphelfer-rescue-ui",
    3001: "setuphelfer-web-ui",
}


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def probe_listening_port(port: int) -> dict[str, Any]:
    """Best-effort local listener probe via ss -ltnp."""
    out = _run(["ss", "-ltnp"])
    pid = None
    process = ""
    for line in out.splitlines():
        if f":{port} " not in line and f":{port}\n" not in line and not re.search(rf":{port}\s", line):
            continue
        m = re.search(r'pid=(\d+).*?"([^"]+)"', line) or re.search(r"pid=(\d+),([^\s]+)", line)
        if m:
            pid = int(m.group(1))
            process = m.group(2)
        break
    unit = ""
    cmdline = ""
    if pid:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace").strip() if Path(f"/proc/{pid}/cmdline").is_file() else ""
        unit_out = _run(["systemctl", "status", str(pid)])
        for uline in unit_out.splitlines():
            if "●" in uline or ".service" in uline:
                unit = uline.strip()
                break
    expected = _DEFAULT_EXPECTED.get(port, "")
    if pid is None:
        state = "free"
    elif expected and expected.lower() in (process + cmdline + unit).lower():
        state = "correct_owner"
    elif pid is not None:
        state = "unexpected_owner"
    else:
        state = "free"
    return {
        "schema_version": PORT_OWNERSHIP_SCHEMA_VERSION,
        "port": port,
        "expected_owner": expected,
        "actual_owner": process or None,
        "pid": pid or 0,
        "unit": unit,
        "cmdline": cmdline,
        "state": state,
        "secrets_exposed": False,
    }


def build_port_ownership_report(ports: list[int] | None = None) -> dict[str, Any]:
    ports = ports or [8000, 8765, 3001]
    items = [probe_listening_port(p) for p in ports]
    conflicts = [i for i in items if i["state"] in {"unexpected_owner", "duplicate_instance"}]
    return {
        "schema_version": PORT_OWNERSHIP_SCHEMA_VERSION,
        "ports": items,
        "conflict_count": len(conflicts),
        "production_ready": False,
        "secrets_exposed": False,
    }


def write_port_ownership_json(dest: Path, ports: list[int] | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(build_port_ownership_report(ports), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest
