#!/bin/bash
# QEMU smoke autopilot — read-only checks + dev-agent send. No USB/dd/mount/apt.
set -u

RUN_ID="${SETUPHELFER_QEMU_SMOKE_RUN_ID:-qemu_smoke_$(date -u +%Y%m%d_%H%M%S)}"
HOST_URL="${SETUPHELFER_DEV_AGENT_SERVER_URL:-http://10.0.2.2:8001}"
export SETUPHELFER_QEMU_SMOKE_RUN_ID="$RUN_ID"

mkdir -p /run/setuphelfer /var/log/setuphelfer 2>/dev/null || true

log_serial() {
  printf '%s\n' "$*" >/dev/ttyS0 2>/dev/null || true
  logger -t setuphelfer-autopilot "$*" 2>/dev/null || true
  printf '%s\n' "$*"
}

log_serial "SETUPHELFER_SYSTEMD_MARKER_START"
log_serial "SETUPHELFER_AUTOPILOT_START run_id=${RUN_ID}"

if command -v loadkeys >/dev/null 2>&1; then
  loadkeys de-latin1 2>/dev/null || loadkeys de 2>/dev/null || true
fi
if command -v setxkbmap >/dev/null 2>&1; then
  setxkbmap -layout de -model pc105 2>/dev/null || true
fi

export PYTHONPATH=/opt/setuphelfer-rescue
export SETUPHELFER_DEV_AGENT_ENABLED=true
export SETUPHELFER_DEV_AGENT_MODE=local_lab
export SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true
export SETUPHELFER_DEV_AGENT_SERVER_URL="${HOST_URL}"
export SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK=true
export SETUPHELFER_DEV_AGENT_QEMU_HOST_URL="${HOST_URL}"

log_serial "SETUPHELFER_DEVSERVER_AGENT_START"
log_serial "SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT"

RESULT_JSON="$(python3 - <<'PY'
import json
import os
import subprocess
from pathlib import Path

run_id = os.environ.get("SETUPHELFER_QEMU_SMOKE_RUN_ID", "qemu_smoke_unknown")
host_url = os.environ.get("SETUPHELFER_DEV_AGENT_SERVER_URL", "http://10.0.2.2:8001")
warnings: list[str] = []
errors: list[str] = []

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()

whoami = "unknown"
rc, out = run(["whoami"])
if rc == 0:
    whoami = out.splitlines()[0] if out else whoami

rc, out = run(["ps", "-p", "1", "-o", "comm="])
pid1 = out.strip() if rc == 0 else "unknown"

rescue_runtime = Path("/opt/setuphelfer-rescue").is_dir()
systemd_running = "unknown"
rc, out = run(["systemctl", "is-system-running"])
if rc in (0, 1):
    systemd_running = out.splitlines()[0] if out else systemd_running

keyboard_layout = ""
kb = Path("/etc/default/keyboard")
if kb.is_file():
    for line in kb.read_text(encoding="utf-8", errors="replace").splitlines():
        if "XKBLAYOUT" in line:
            keyboard_layout = line.strip()
            break

host_health_ok = False
host_health_raw = ""
rc, out = run(["curl", "-sS", "-m", "8", f"{host_url.rstrip('/')}/api/dev-server/health"])
host_health_raw = out
if rc == 0:
    try:
        json.loads(out)
        host_health_ok = True
    except json.JSONDecodeError:
        warnings.append("host_health_not_json")
else:
    warnings.append("host_health_curl_failed")

agent_send_ok = False
agent_send_raw = ""
rc, out = run([
    "python3", "-m", "backend.devserver_agent.cli",
    "--mode", "local_lab",
    "--server", host_url,
    "--qemu-host-fallback",
    "--qemu-host-url", host_url,
    "--send", "--json",
])
agent_send_raw = out
if rc == 0:
    agent_send_ok = True
else:
    warnings.append("agent_send_failed")

spool_files: list[str] = []
if not agent_send_ok:
    root = Path("/opt/setuphelfer-rescue")
    if root.is_dir():
        for fp in root.rglob("*dev-agent-spool*"):
            if fp.is_file():
                spool_files.append(str(fp))
                if len(spool_files) >= 5:
                    break
    if spool_files:
        warnings.append("spool_present")

status = "review_required"
if rescue_runtime and pid1 == "systemd" and host_health_ok and agent_send_ok:
    status = "success"
elif not rescue_runtime or pid1 != "systemd":
    status = "failed"

payload = {
    "run_id": run_id,
    "status": status,
    "autopilot": True,
    "whoami": whoami,
    "systemd_pid1": pid1,
    "systemd_running": systemd_running,
    "rescue_runtime_present": rescue_runtime,
    "keyboard_layout_file": keyboard_layout,
    "host_dev_server_url": host_url,
    "host_health_ok": host_health_ok,
    "host_health_raw": host_health_raw[:2000],
    "agent_send_ok": agent_send_ok,
    "agent_send_raw": agent_send_raw[:4000],
    "spool_files": spool_files,
    "warnings": warnings,
    "errors": errors,
    "usb_write_started": False,
    "dd_executed": False,
    "backup_started": False,
    "restore_started": False,
}
print(json.dumps(payload, ensure_ascii=False))
PY
)"

if echo "$RESULT_JSON" | grep -q '"agent_send_ok": true'; then
  log_serial "SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT ok"
else
  log_serial "SETUPHELFER_DEVSERVER_AGENT_ERROR:agent_send_failed"
fi

for dest in /run/setuphelfer/qemu-smoke-result.json /var/log/setuphelfer/qemu-smoke-result.json; do
  printf '%s\n' "$RESULT_JSON" >"$dest" 2>/dev/null || true
done

SERIAL_LINE="SETUPHELFER_QEMU_SMOKE_RESULT_JSON_BEGIN ${RESULT_JSON} SETUPHELFER_QEMU_SMOKE_RESULT_JSON_END"
printf '%s\n' "$SERIAL_LINE"
if [[ -c /dev/ttyS0 ]]; then
  printf '%s\n' "$SERIAL_LINE" > /dev/ttyS0 2>/dev/null || true
fi

exit 0
