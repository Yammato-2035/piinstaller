"""
Network Discovery Core — canonical read-only network discovery implementation.

Phase G.8: logic extracted from ``app.py``; no network writes, no new discovery rules.
"""

from __future__ import annotations

import re
import subprocess
import time
from typing import Any

DISCOVERY_VERSION = 1


def _get_discovery_logger():
    try:
        from debug.logger import get_logger

        return get_logger("network", "detect")
    except Exception:
        return type(
            "NoopLogger",
            (),
            {
                "step_start": lambda *a, **k: None,
                "step_end": lambda *a, **k: None,
                "decision": lambda *a, **k: None,
                "apply_noop": lambda *a, **k: None,
                "error": lambda *a, **k: None,
            },
        )()


def _shell_run(cmd: str, *, timeout: int = 10) -> dict[str, Any]:
    """Shell command runner (legacy ``app.run_command`` shape for non-sudo probes)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout", "stdout": "", "stderr": ""}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc), "stdout": "", "stderr": ""}


def _is_reachable_lan_ip(ip: str) -> bool:
    """Filter unusable addresses. 0.0.0.0 is not a reachable home-network address."""
    if not ip or not ip.strip():
        return False
    s = ip.strip().lower()
    if s in ("0.0.0.0", "127.0.0.1", "::1", "localhost"):
        return False
    if s.startswith("127.") or s.startswith("fe80:"):
        return False
    if s.startswith("169.254."):
        return False
    return True


def discover_demo_network() -> dict[str, Any]:
    """Demo network placeholder (legacy ``_demo_network`` shape)."""
    return {"ips": ["192.168.1.100"], "hostname": "raspberrypi"}


def detect_frontend_port() -> int:
    """Detect frontend port: 5173 (Tauri/Vite dev) preferred, else 3001/3002."""
    try:
        r = _shell_run("ss -tuln 2>/dev/null | grep -E ':5173|:3001|:3002'")
        if r.get("success") and r.get("stdout"):
            out = r["stdout"]
            if ":5173" in out:
                return 5173
            if ":3001" in out:
                return 3001
            if ":3002" in out:
                return 3002
    except Exception:
        pass
    return 3001


def discover_network_info() -> dict[str, Any]:
    """Network info for UI/API including robust LAN detection in service context."""
    log = _get_discovery_logger()
    log.step_start("get_network_info")
    t0 = time.perf_counter()
    try:
        warnings: list[str] = []
        interfaces: list[dict[str, str]] = []
        source = "none"
        ips: list[str] = []

        ip_result = _shell_run(
            "/usr/sbin/ip -4 -o addr show scope global 2>/dev/null || "
            "/sbin/ip -4 -o addr show scope global 2>/dev/null || "
            "ip -4 -o addr show scope global 2>/dev/null"
        )
        raw_ip_lines = (ip_result.get("stdout") or "").splitlines() if ip_result.get("success") else []
        excluded_if_prefixes = ("lo", "docker", "veth", "br-", "virbr", "wg", "tailscale")
        seen_ips: set[str] = set()

        for line in raw_ip_lines:
            m = re.search(r"^\s*\d+:\s+([^\s:]+)\s+inet\s+([0-9.]+)/\d+", line)
            if not m:
                continue
            iface = (m.group(1) or "").split("@", 1)[0]
            addr = m.group(2) or ""
            iface_l = iface.lower()
            if iface_l.startswith(excluded_if_prefixes):
                continue
            if not _is_reachable_lan_ip(addr):
                continue
            if addr in seen_ips:
                continue
            seen_ips.add(addr)
            ips.append(addr)
            interfaces.append({"name": iface, "ip": addr, "source": "ip-addr-global"})

        if ips:
            source = "ip-addr-global"

        if not ips:
            log.decision("source_filter", data={"source": "hostname -I fallback", "filter": "reachable_lan_only"})
            result = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
            raw = (result.stdout or "").strip()
            candidates = [x for x in raw.split() if x] if raw else []
            for addr in candidates:
                if not _is_reachable_lan_ip(addr):
                    continue
                if addr in seen_ips:
                    continue
                seen_ips.add(addr)
                ips.append(addr)
                interfaces.append({"name": "unknown", "ip": addr, "source": "hostname-I"})
            if ips:
                source = "hostname-I"

        if not ips:
            warnings.append("Nur lokal erreichbar - keine LAN-IP erkannt")
            source = "none"

        log.decision(
            "network_source",
            data={"source": source, "ip_count": len(ips), "interface_count": len(interfaces)},
        )

        result = subprocess.run(["hostname"], capture_output=True, text=True, timeout=5)
        hostname = (result.stdout or "").strip() or "unknown"
        out = {
            "ips": ips,
            "localhost": "127.0.0.1",
            "primary_ip": ips[0] if ips else None,
            "interfaces": interfaces,
            "warnings": warnings,
            "source": source,
            "hostname": hostname,
        }
        log.apply_noop("get_network_info", data={"reason": "read_only_discovery"})
        log.step_end(
            "get_network_info",
            duration_ms=(time.perf_counter() - t0) * 1000,
            data={"hostname": hostname, "ip_count": len(ips)},
        )
        return out
    except Exception as exc:  # noqa: BLE001
        log.step_end("get_network_info", duration_ms=(time.perf_counter() - t0) * 1000, data={"error": str(exc)})
        return {"ips": [], "hostname": "unknown"}


def build_network_discovery_diagnostics() -> dict[str, Any]:
    """Lightweight discovery diagnostics — no active probe."""
    return {
        "discovery_version": DISCOVERY_VERSION,
        "discovery_module": "core.network_discovery",
        "public_functions": [
            "discover_network_info",
            "discover_demo_network",
            "detect_frontend_port",
            "build_network_discovery_diagnostics",
        ],
        "legacy_wrappers_in_app": [
            "get_network_info",
            "_demo_network",
            "_detect_frontend_port",
        ],
        "read_only": True,
        "writes_allowed": False,
        "network_writes_allowed": False,
        "app_import_required": False,
    }
