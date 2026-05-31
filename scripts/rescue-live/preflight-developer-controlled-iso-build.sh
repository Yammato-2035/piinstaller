#!/usr/bin/env bash
# Read-only preflight for Rescue Developer controlled ISO build.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT="${REPO_ROOT}/docs/evidence/runtime-results/rescue/rescue_developer_controlled_iso_build_preflight.json"
RUN_ID="${1:-rescue_developer_iso_$(date -u +%Y%m%d_%H%M%S)}"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
PRIOR_INV="${REPO_ROOT}/docs/evidence/runtime-results/rescue/prior-artifacts/prior_rescue_artifacts_before_controlled_developer_iso_build.json"

cd "$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}"

python3 - "$OUT" "$RUN_ID" "$BUILD_ROOT" "$PRIOR_INV" "$REPO_ROOT" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

out_path = Path(sys.argv[1])
run_id = sys.argv[2]
build_root = Path(sys.argv[3])
prior_inv = Path(sys.argv[4])
repo = Path(sys.argv[5])

errors: list[str] = []
warnings: list[str] = []

def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()

rg, _ = run(["./scripts/check-runtime-deploy-gate.sh"])
bg, _ = run(["./scripts/check-backend-version-gate.sh"])
gg, _ = run(["./scripts/check-dev-agent-rescue-profile-guard.sh"])

if rg != 0:
    errors.append("runtime_gate_failed")
if bg != 0:
    errors.append("backend_version_gate_failed")
if gg != 0:
    errors.append("dev_agent_profile_guard_failed")

dev_env = build_root / "config/includes.chroot/etc/setuphelfer/setuphelfer-dev-agent.env"
dev_svc = build_root / "config/includes.chroot/etc/systemd/system/setuphelfer-dev-agent.service"
dev_marker = build_root / "config/includes.chroot/opt/setuphelfer-rescue/config/rescue-developer-profile.json"

if not dev_env.is_file():
    errors.append("developer_env_not_in_build_tree")
if not dev_svc.is_file():
    errors.append("developer_systemd_not_in_build_tree")
if not dev_marker.is_file():
    warnings.append("developer_profile_marker_missing")

prior_count = 0
if prior_inv.is_file():
    prior_count = json.loads(prior_inv.read_text(encoding="utf-8")).get("prior_artifact_count", 0)

status = "blocked" if errors else ("review_required" if warnings else "ready")
if prior_count:
    warnings.append(f"prior_artifacts_inventoried:{prior_count}")

body = {
    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    "run_id": run_id,
    "status": status,
    "runtime_gate_ok": rg == 0,
    "backend_version_gate_ok": bg == 0,
    "profile_guard_ok": gg == 0,
    "clean_runtime_assumed": True,
    "developer_profile_in_tree": dev_env.is_file() and dev_svc.is_file(),
    "prior_artifact_inventory": str(prior_inv) if prior_inv.is_file() else None,
    "prior_artifact_count": prior_count,
    "usb_target_set": False,
    "dd_planned": False,
    "mount_planned": False,
    "public_telemetry_planned": False,
    "build_entrypoint": "scripts/rescue-live/run-controlled-iso-build-with-logging.sh",
    "build_profile": "developer",
    "warnings": warnings,
    "errors": errors,
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "path": str(out_path)}, indent=2))
if status == "blocked":
    sys.exit(20)
if status == "review_required":
    sys.exit(10)
PY
