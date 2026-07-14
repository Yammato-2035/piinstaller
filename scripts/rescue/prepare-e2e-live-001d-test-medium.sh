#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D4 — Register external test medium with e2e-target marker.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEVICE=""
EXECUTE=false
MOUNT=""

usage() {
  echo "Usage: $0 --device /dev/sdXn [--execute]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) DEVICE="$2"; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$DEVICE" ]] || usage
[[ -b "$DEVICE" ]] || { echo "ERROR: not a block device: $DEVICE" >&2; exit 1; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
export PREP_DEVICE="$DEVICE"
export PREP_EXECUTE="$EXECUTE"

python3 - <<'PY'
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from core.rescue_physical_e2e_test_target import build_e2e_target_marker, write_e2e_target_marker

device = os.environ["PREP_DEVICE"]
execute = os.environ.get("PREP_EXECUTE", "false").lower() == "true"

proc = subprocess.run(["blkid", "-o", "value", "-s", "UUID", device], capture_output=True, text=True, check=False)
uuid = (proc.stdout or "").strip()
if not uuid:
    print(json.dumps({"ok": False, "error": "uuid_not_found"}))
    sys.exit(1)

mount = tempfile.mkdtemp(prefix="setuphelfer-e2e-prep-")
mounted = False
try:
    if execute:
        subprocess.run(["sudo", "mount", device, mount], check=True)
        mounted = True
    marker = build_e2e_target_marker(filesystem_uuid=uuid)
    if execute:
        write_e2e_target_marker(Path(mount), marker)
    print(json.dumps({
        "ok": True,
        "executed": execute,
        "device": device,
        "filesystem_uuid": uuid,
        "marker_schema": marker["schema"],
        "allowed_root": marker["allowed_root"],
        "max_test_bytes": marker["max_test_bytes"],
        "serial_in_evidence": False,
    }, indent=2))
finally:
    if mounted:
        subprocess.run(["sudo", "umount", mount], check=False)
    Path(mount).rmdir() if Path(mount).exists() else None
PY
