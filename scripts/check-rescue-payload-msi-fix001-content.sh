#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<'PY'
import json
import sys
from pathlib import Path

from core.rescue_payload_msi_fix_content import (
    default_repacked_squashfs_path,
    verify_rescue_payload_msi_fix_content,
)

squashfs = Path(__import__("os").environ.get("SETUPHELFER_RESCUE_PAYLOAD_SQUASHFS", "")) \
    if __import__("os").environ.get("SETUPHELFER_RESCUE_PAYLOAD_SQUASHFS") \
    else default_repacked_squashfs_path()

if not squashfs.is_file():
    print(json.dumps({"content_ok": False, "error": "squashfs_missing", "path": str(squashfs)}, indent=2))
    sys.exit(17)

result = verify_rescue_payload_msi_fix_content(squashfs)
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result.get("content_ok") else 18)
PY
