#!/usr/bin/env bash
# Optional RS-001 QEMU menu smoke — no USB write, no target disk.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
  echo '{"qemu_smoke":"blocked_missing_qemu","hardware_retest_allowed":false}'
  exit 0
fi

ISO="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
if [[ ! -f "$ISO" ]]; then
  echo '{"qemu_smoke":"blocked_missing_iso","iso_path":"'"$ISO"'"}'
  exit 0
fi

EVIDENCE_DIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue/rs001_qemu_menu_smoke_latest"
mkdir -p "$EVIDENCE_DIR"
SERIAL_LOG="${EVIDENCE_DIR}/serial.log"
TIMEOUT_SEC="${RS001_QEMU_SMOKE_TIMEOUT:-180}"

echo "Starting QEMU menu smoke (timeout ${TIMEOUT_SEC}s, no disk)..." >&2
timeout "$TIMEOUT_SEC" qemu-system-x86_64 \
  -m 2048 \
  -smp 2 \
  -cdrom "$ISO" \
  -boot d \
  -serial "file:${SERIAL_LOG}" \
  -display none \
  -no-reboot \
  -snapshot \
  2>"${EVIDENCE_DIR}/qemu.stderr" || true

python3 - <<PY
import json
from pathlib import Path

log_path = Path(${SERIAL_LOG@Q})
text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
signals = {
    "grub_or_linux": any(s in text.lower() for s in ("grub", "vmlinuz", "setuphelfer")),
    "setuphelfer_rescue": "setuphelfer" in text.lower(),
    "fallback_or_url": "fallback" in text.lower() or "8765" in text or "rescue.html" in text,
    "network_failed_before_menu": "network-onboarding.service failed" in text.lower(),
    "telemetry_failed_before_menu": "telemetry-push.service failed" in text.lower(),
}
ok = signals["grub_or_linux"] and not signals["network_failed_before_menu"]
print(json.dumps({
    "qemu_smoke": "ok" if ok else "review_required",
    "signals": signals,
    "serial_log": str(log_path),
    "log_bytes": len(text.encode("utf-8")),
}, indent=2))
PY
