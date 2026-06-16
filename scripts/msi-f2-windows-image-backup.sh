#!/usr/bin/env bash
# F.2 MSI Windows image backup — gated execution (read source, write file on external mount only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONFIRM1="${OPERATOR_CONFIRMATION_1:-}"
CONFIRM2="${OPERATOR_CONFIRMATION_2:-}"

python3 <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path("backend").resolve()))
from core.msi_windows_image_backup import (
    F2_SOURCE_DEVICE,
    OPERATOR_CONFIRMATION_1,
    OPERATOR_CONFIRMATION_2,
    discover_external_backup_mount,
    initial_status_payload,
    run_f2_preflight,
)

def lsblk_bytes(dev: str) -> int:
    out = subprocess.check_output(
        ["lsblk", "-b", "-n", "-o", "SIZE", dev],
        text=True,
    ).strip().splitlines()
    return int(out[0]) if out else 0

def df_free_bytes(mount_path: str) -> int:
    for cmd in (["df", "-B1", mount_path], ["sudo", "-n", "df", "-B1", mount_path]):
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return int(out.splitlines()[-1].split()[3])
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError, ValueError):
            continue
    raise SystemExit("blocked_external_target_mount_missing")


def find_backup_mount() -> tuple[str, str, str, int]:
    data = json.loads(subprocess.check_output(["findmnt", "-J"], text=True))
    discovered = discover_external_backup_mount(data)
    if not discovered:
        raise SystemExit("blocked_external_target_mount_missing")
    tgt, src, fst = discovered
    free_b = df_free_bytes(tgt)
    return tgt, src, fst, free_b

mount, tgt_dev, fstype, free_b = find_backup_mount()
src_size = lsblk_bytes(F2_SOURCE_DEVICE)
c1 = os.environ.get("OPERATOR_CONFIRMATION_1", "")
c2 = os.environ.get("OPERATOR_CONFIRMATION_2", "")

pf = run_f2_preflight(
    source_device=F2_SOURCE_DEVICE,
    source_size_bytes=src_size,
    target_mount=mount,
    target_device=tgt_dev,
    free_bytes=free_b,
    fstype=fstype,
    operator_confirmation_1=c1,
    operator_confirmation_2=c2,
)

job_id = f"F2-MSI-{pf.source_device.replace('/dev/', '')}"
result = {
    "run_id": job_id,
    "preflight": pf.to_dict(),
    "operator_confirmations_required": [OPERATOR_CONFIRMATION_1, OPERATOR_CONFIRMATION_2],
}

evidence_dir = Path("docs/evidence/msi")
evidence_dir.mkdir(parents=True, exist_ok=True)
out_json = evidence_dir / "F2_MSI_WINDOWS_IMAGE_BACKUP_RESULT.json"
out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if not pf.ok:
    print(json.dumps({"status": "blocked", "reason": pf.reason, "preflight": pf.to_dict()}, indent=2))
    sys.exit(17 if pf.reason == "blocked_insufficient_target_capacity" else 18)

# Ready for dd — create backup dir only when preflight ok
backup_dir = Path(pf.backup_dir or "")
backup_dir.mkdir(parents=True, exist_ok=True)
status_path = Path(pf.paths["status_json"])
status_path.write_text(json.dumps(initial_status_payload(pf, job_id), indent=2) + "\n", encoding="utf-8")

partial = Path(pf.paths["image_partial"])
print(json.dumps({"status": "ready", "partial": str(partial), "backup_dir": str(backup_dir)}, indent=2))
print("EXECUTE_DD_MANUALLY_OR_VIA_OPERATOR", file=sys.stderr)
PY
