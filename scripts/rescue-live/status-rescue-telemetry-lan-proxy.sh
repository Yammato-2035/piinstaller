#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}:${PYTHONPATH:-}"

python3 - <<'PY'
import json
from core.rescue_telemetry_lan_proxy import (
    DEFAULT_PORT,
    DEFAULT_UPSTREAM,
    build_status_payload,
    detect_lan_ip,
    health_url,
    ingest_url,
    probe_lan_health,
    read_pid_file,
    backend_local_health_ok,
    write_status_file,
)

port = DEFAULT_PORT
upstream = DEFAULT_UPSTREAM
bind = detect_lan_ip()
pid = read_pid_file()
running = pid is not None

# Prefer systemd MainPID when the unit is installed and active.
try:
    import subprocess

    unit = "setuphelfer-rescue-telemetry-lan-proxy.service"
    proc = subprocess.run(
        ["systemctl", "show", unit, "-p", "ActiveState", "-p", "MainPID", "--value"],
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    if proc.returncode == 0:
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if len(lines) >= 2 and lines[0] == "active":
            main_pid = int(lines[1])
            if main_pid > 0:
                pid = main_pid
                running = True
except (OSError, subprocess.SubprocessError, ValueError):
    pass

backend_ok = backend_local_health_ok(upstream)
lan_ok = probe_lan_health(bind, port) if running and bind else False
blockers = []
if not backend_ok:
    blockers.append("BACKEND_HEALTH_FAILED")
if running and not lan_ok:
    blockers.append("LAN_HEALTH_FAILED")
if not running:
    blockers.append("PROXY_NOT_RUNNING")

payload = build_status_payload(
    running=running,
    pid=pid,
    bind_host=bind,
    port=port,
    upstream=upstream,
    backend_health_ok=backend_ok,
    lan_health_ok=lan_ok,
    blockers=blockers,
)
write_status_file(payload)
print(json.dumps(payload, indent=2, ensure_ascii=False))
PY
