"""IONOS / public telemetry preflight for physical E2E (read-only)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from core.rescue_telemetry_cloud_reachability import probe_cloud_telemetry_health


def load_ionos_env(path: Path | None = None) -> dict[str, str]:
    env_path = path or Path.home() / ".config/setuphelfer/e2e-live-001c-ionos.env"
    out: dict[str, str] = {}
    if not env_path.is_file():
        return out
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _ssh_check(host: str, user: str, identity: str, remote_cmd: str, timeout: int = 20) -> dict[str, Any]:
    cmd = [
        "ssh",
        "-i",
        identity,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={timeout}",
        f"{user}@{host}",
        remote_cmd,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout + 5)
    return {
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_lines": len((proc.stdout or "").splitlines()),
        "stderr_present": bool(proc.stderr),
    }


def run_pre_physical_server_preflight(
    *,
    ionos_env: dict[str, str] | None = None,
    external_calls: bool = True,
) -> dict[str, Any]:
    env = ionos_env or load_ionos_env()
    base_url = env.get("SETUPHELFER_PUBLIC_TELEMETRY_BASE_URL", "https://telemetrie.setuphelfer.de")
    host = env.get("SETUPHELFER_IONOS_SSH_HOST", "")
    user = env.get("SETUPHELFER_IONOS_SSH_USER", "")
    identity = env.get("SETUPHELFER_IONOS_SSH_IDENTITY_FILE", "")

    telemetry_probe = probe_cloud_telemetry_health(
        base_url=base_url,
        external_calls=external_calls,
        environ={**os.environ, "SETUPHELFER_RESCUE_TELEMETRY_EXTERNAL_CALLS": "true" if external_calls else "false"},
    )

    ssh_ok = False
    telemetry_active = False
    diagnostics_active = False
    if host and user and identity and Path(identity).expanduser().is_file():
        ssh_ok = _ssh_check(host, user, str(Path(identity).expanduser()), "true").get("ok", False)
        if ssh_ok:
            telemetry_active = _ssh_check(
                host, user, str(Path(identity).expanduser()),
                "systemctl is-active setuphelfer-telemetry-server 2>/dev/null || systemctl is-active telemetry-server 2>/dev/null",
            ).get("ok", False)
            diagnostics_active = _ssh_check(
                host, user, str(Path(identity).expanduser()),
                "systemctl is-active setuphelfer-diagnostics-server 2>/dev/null || systemctl is-active diagnostics-server 2>/dev/null",
            ).get("ok", False)

    telemetry_ready = bool(telemetry_probe.get("reachable")) and telemetry_probe.get("classification") == "ok"
    diagnostics_ready = diagnostics_active or ssh_ok

    blockers: list[str] = []
    if not telemetry_ready:
        blockers.append("live_telemetry_preflight_failed")
    if host and not diagnostics_ready:
        blockers.append("live_diagnostics_preflight_failed")

    return {
        "schema": "setuphelfer.rescue.pre-physical-preflight.v1",
        "telemetry_public": {
            "base_url": base_url,
            "reachable": telemetry_probe.get("reachable"),
            "classification": telemetry_probe.get("classification"),
            "http_status": telemetry_probe.get("http_status"),
            "legacy_mock": False,
        },
        "ionos_ssh": {
            "configured": bool(host and user and identity),
            "reachable": ssh_ok,
            "telemetry_service_active": telemetry_active,
            "diagnostics_service_active": diagnostics_active,
        },
        "live_pipeline_ready_for_physical_rescue_test": telemetry_ready and (not host or diagnostics_ready),
        "blockers": blockers,
        "production_ready": False,
    }
