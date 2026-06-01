#!/usr/bin/env bash
# Setuphelfer rescue remote agent — allowlisted runbooks only (local_lab phase 1).
set -euo pipefail

ENV_FILE="${SETUPHELFER_RESCUE_REMOTE_ENV:-/run/setuphelfer/rescue-remote.env}"
LOG_TAG="setuphelfer-rescue-remote-agent"

die() { logger -t "$LOG_TAG" "ERROR: $*"; echo "ERROR: $*" >&2; exit 1; }

# shellcheck disable=SC1090
[[ -f "$ENV_FILE" ]] && set -a && . "$ENV_FILE" && set +a

[[ "${SETUPHELFER_REMOTE_ENABLED:-0}" == "1" ]] || die "remote control disabled"
[[ -n "${SETUPHELFER_DEV_SERVER_URL:-}" ]] || die "SETUPHELFER_DEV_SERVER_URL missing"
[[ -n "${SETUPHELFER_REMOTE_AGENT_ID:-}" ]] || die "SETUPHELFER_REMOTE_AGENT_ID missing"

export AGENT_ID="${SETUPHELFER_REMOTE_AGENT_ID}"
export BOOT_ID="${SETUPHELFER_REMOTE_BOOT_ID:-boot_$(date -u +%Y%m%d_%H%M%S)}"
export DEV_URL="${SETUPHELFER_DEV_SERVER_URL}"
export PAIRING_TOKEN="${SETUPHELFER_PAIRING_TOKEN:-}"
export CMD_TIMEOUT="${SETUPHELFER_REMOTE_CMD_TIMEOUT:-30}"

python3 <<'PY' || die "agent cycle failed"
import json, os, re, subprocess, urllib.request

dev_url = os.environ["DEV_URL"].rstrip("/")
agent_id = os.environ["AGENT_ID"]
boot_id = os.environ["BOOT_ID"]
timeout_s = int(os.environ.get("CMD_TIMEOUT", "30"))
allow = {
    "collect_boot_logs", "collect_network_status", "collect_storage_inventory_readonly",
    "collect_devserver_agent_logs", "collect_qemu_or_rescue_agent_status",
    "test_devserver_connectivity",
}
blocked = {
    "shell", "arbitrary_command", "run_command", "write_usb", "restore_execute",
    "dd", "mkfs", "apt_install", "mount_rw", "partition_write", "format",
}


def post(path, body):
    req = urllib.request.Request(
        dev_url + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def get(path):
    with urllib.request.urlopen(dev_url + path, timeout=30) as resp:
        return json.loads(resp.read().decode())


def redact(text):
    for pat in (
        r"(?i)(password|passwd|psk|token|secret)\s*[:=]\s*\S+",
        r"Bearer\s+\S+",
    ):
        text = re.sub(pat, "[REDACTED]", text)
    return text[:65536]


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        return p.returncode, redact((p.stdout or "") + (p.stderr or "")), ""
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError as e:
        return 127, "", str(e)


def exec_rb(rid):
    if rid in blocked:
        return 126, "", f"blocked:{rid}"
    if rid == "upload_rescue_evidence_bundle":
        return 2, "", "not_implemented_phase1"
    if rid not in allow:
        return 127, "", f"unknown:{rid}"
    if rid == "collect_boot_logs":
        c1, o1, e1 = run(["journalctl", "-b", "--no-pager", "-n", "300"])
        c2, o2, e2 = run(["dmesg", "--ctime"])
        tail = "\n".join((o2 or "").splitlines()[-300:])
        return max(c1, c2), (o1 or "") + "\n" + tail, (e1 or e2)
    if rid == "collect_network_status":
        parts, ec = [], 0
        for cmd in (["ip", "addr"], ["ip", "route"]):
            c, o, e = run(cmd)
            ec = max(ec, c)
            parts.append(o)
        c, o, e = run(["nmcli", "device", "status"])
        if c == 0:
            parts.append(o)
        return ec, "\n".join(parts), ""
    if rid == "collect_storage_inventory_readonly":
        c1, o1, e1 = run(["lsblk", "-o", "NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL"])
        c2, o2, e2 = run(["findmnt"])
        return max(c1, c2), (o1 or "") + "\n" + (o2 or ""), (e1 or e2)
    if rid in ("collect_devserver_agent_logs", "collect_qemu_or_rescue_agent_status"):
        return run(["journalctl", "-u", "setuphelfer-rescue-remote-agent", "--no-pager", "-n", "200"])
    if rid == "test_devserver_connectivity":
        return run(["curl", "-fsS", f"{dev_url}/api/version"])
    return 127, "", "unknown"


post("/api/rescue-remote/register", {
    "agent_id": agent_id,
    "boot_id": boot_id,
    "mode": "local_lab",
    "pairing_token": os.environ.get("PAIRING_TOKEN", ""),
    "capabilities": {
        "read_logs": True,
        "run_readonly_runbooks": True,
        "run_write_runbooks": False,
        "network_info": True,
    },
    "network": {"interface": "unknown", "ip": "", "gateway": "", "dev_server_url": dev_url},
    "security": {
        "paired": bool(os.environ.get("PAIRING_TOKEN")),
        "remote_shell": False,
        "controlled_write": False,
    },
})
post("/api/rescue-remote/heartbeat", {"agent_id": agent_id, "boot_id": boot_id, "status": "online"})

for job in get(f"/api/rescue-remote/jobs?agent_id={agent_id}").get("jobs", []):
    if job.get("status") != "queued":
        continue
    jid, rid = job["job_id"], job["runbook_id"]
    post(f"/api/rescue-remote/jobs/{jid}/claim?agent_id={agent_id}", {})
    code, out, err = exec_rb(rid)
    post(f"/api/rescue-remote/jobs/{jid}/result", {
        "agent_id": agent_id,
        "status": "success" if code == 0 else "failed",
        "result": {
            "exit_code": code,
            "stdout_excerpt": out,
            "stderr_excerpt": err,
            "warnings": [],
            "errors": [],
        },
    })
PY

logger -t "$LOG_TAG" "OK agent_id=${AGENT_ID}"
