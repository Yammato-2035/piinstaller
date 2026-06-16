#!/usr/bin/env bash
# Headless VM boot test for the STANDARD rescue ISO.
#
# Reproduces the MSI hardware boot in a local VM and captures a fully verbose
# serial log (no quiet/splash, console=ttyS0) so we can see exactly where the
# boot stops — instead of guessing from a blinking cursor.
#
# Two boot paths are supported:
#   --mode direct  (default) : QEMU direct kernel boot (-kernel/-initrd) with an
#                              overridable cmdline; ISO attached so live-boot finds
#                              the squashfs. Fast, no rebuild needed, full log.
#   --mode uefi              : full OVMF/UEFI boot of the ISO itself (mirrors MSI
#                              firmware path; uses whatever cmdline GRUB sets).
#
# Variants (--variant): default | network | msi-compat | diagnose
#
# No USB write, no target disk, runs with -snapshot (ISO untouched).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ISO="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
MODE="direct"
VARIANT="default"
TIMEOUT_SEC="${RESCUE_VM_TIMEOUT:-180}"
MEM_MIB="${RESCUE_VM_MEM:-3072}"
SMP="${RESCUE_VM_SMP:-2}"
EXTRA_APPEND=""
OVMF_CODE="/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS_SRC="/usr/share/OVMF/OVMF_VARS_4M.fd"

usage() {
  cat <<EOF
Usage: $0 [options]
  --iso PATH            ISO path (default: $ISO)
  --mode direct|uefi    Boot method (default: direct)
  --variant NAME        default | network | msi-compat | diagnose (default: default)
  --timeout SEC         VM run timeout (default: ${TIMEOUT_SEC})
  --append "..."        Extra kernel cmdline appended (direct mode only)
  -h|--help
EOF
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --variant) VARIANT="$2"; shift 2 ;;
    --timeout) TIMEOUT_SEC="$2"; shift 2 ;;
    --append) EXTRA_APPEND="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) echo "unknown arg: $1" >&2; usage 1 ;;
  esac
done

command -v qemu-system-x86_64 >/dev/null 2>&1 || { echo '{"vm_test":"blocked_missing_qemu"}'; exit 0; }
[[ -f "$ISO" ]] || { echo "{\"vm_test\":\"blocked_missing_iso\",\"iso_path\":\"${ISO}\"}"; exit 0; }

STAMP="$(date +%Y%m%d_%H%M%S)"
EVIDENCE_DIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue/vm_standard_boot_${STAMP}"
LATEST_DIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue/vm_standard_boot_latest"
mkdir -p "$EVIDENCE_DIR"
SERIAL_LOG="${EVIDENCE_DIR}/serial.log"
QEMU_ERR="${EVIDENCE_DIR}/qemu.stderr"
WORK="$(mktemp -d /tmp/rescue_vm_XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

# variant-specific kernel args (mirror grub menu snippet)
VARIANT_APPEND="setuphelfer_start_assistant=1"
case "$VARIANT" in
  default) ;;
  network) VARIANT_APPEND="setuphelfer_network_onboarding=1 setuphelfer_start_assistant=1" ;;
  msi-compat) VARIANT_APPEND="pci=noaer nomodeset setuphelfer_msi_compat=1" ;;
  diagnose) VARIANT_APPEND="setuphelfer_diagnose=1 systemd.log_level=debug" ;;
  *) echo "unknown variant: $VARIANT" >&2; exit 2 ;;
esac

# Verbose console so the boot is fully visible on serial (the whole point).
VERBOSE_CONSOLE="console=tty0 console=ttyS0,115200n8 loglevel=7 systemd.show_status=true ignore_loglevel printk.devkmsg=on"

KVM_ARGS=()
[[ -r /dev/kvm && -w /dev/kvm ]] && KVM_ARGS+=(-enable-kvm -cpu host)

echo "=== Rescue STANDARD ISO VM test ===" >&2
echo "mode=${MODE} variant=${VARIANT} timeout=${TIMEOUT_SEC}s iso=${ISO}" >&2
echo "evidence=${EVIDENCE_DIR}" >&2

run_direct() {
  echo "Extracting kernel/initrd from ISO..." >&2
  xorriso -osirrox on -indev "$ISO" \
    -extract /live/vmlinuz "$WORK/vmlinuz" \
    -extract /live/initrd.img "$WORK/initrd.img" 2>>"$QEMU_ERR"
  local append="boot=live components ${VERBOSE_CONSOLE} setuphelfer_rescue=1 ${VARIANT_APPEND} ${EXTRA_APPEND}"
  echo "append: ${append}" >&2
  echo "$append" > "${EVIDENCE_DIR}/kernel_cmdline.txt"
  timeout "$TIMEOUT_SEC" qemu-system-x86_64 \
    "${KVM_ARGS[@]}" \
    -m "$MEM_MIB" -smp "$SMP" \
    -kernel "$WORK/vmlinuz" -initrd "$WORK/initrd.img" \
    -append "$append" \
    -drive file="$ISO",media=cdrom,readonly=on \
    -serial "file:${SERIAL_LOG}" \
    -display none -no-reboot -snapshot \
    2>>"$QEMU_ERR" || true
}

run_uefi() {
  cp "$OVMF_VARS_SRC" "$WORK/OVMF_VARS.fd"
  echo "UEFI/OVMF boot (firmware path as on MSI). GRUB cmdline used as-is." >&2
  timeout "$TIMEOUT_SEC" qemu-system-x86_64 \
    "${KVM_ARGS[@]}" \
    -m "$MEM_MIB" -smp "$SMP" \
    -drive if=pflash,format=raw,unit=0,readonly=on,file="$OVMF_CODE" \
    -drive if=pflash,format=raw,unit=1,file="$WORK/OVMF_VARS.fd" \
    -drive file="$ISO",media=cdrom,readonly=on \
    -boot d \
    -serial "file:${SERIAL_LOG}" \
    -display none -no-reboot -snapshot \
    2>>"$QEMU_ERR" || true
}

case "$MODE" in
  direct) run_direct ;;
  uefi) run_uefi ;;
  *) echo "unknown mode: $MODE" >&2; exit 2 ;;
esac

# Refresh "latest" pointer
rm -rf "$LATEST_DIR"; cp -a "$EVIDENCE_DIR" "$LATEST_DIR"

python3 - "$SERIAL_LOG" "$EVIDENCE_DIR" "$MODE" "$VARIANT" <<'PY'
import json, re, sys
from pathlib import Path

log_path = Path(sys.argv[1]); evdir = Path(sys.argv[2]); mode = sys.argv[3]; variant = sys.argv[4]
text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
low = text.lower()

# Collect failed/error lines
failed_units = sorted(set(re.findall(r'([A-Za-z0-9@._\-]+\.service)(?=.*(?:failed|not be started))', text, re.IGNORECASE)))
failed_lines = [ln for ln in text.splitlines() if re.search(r'\b(failed|error|cannot|unable|panic|oops|timed out|dependency)\b', ln, re.IGNORECASE)]

signals = {
    "kernel_started": "linux version" in low or "command line" in low,
    "initramfs_reached": "initramfs" in low or "live-boot" in low or "/init" in low,
    "live_medium_found": "filesystem.squashfs" in low or "rootfs" in low or "live medium" in low,
    "systemd_started": "systemd[1]" in low or "welcome to" in low,
    "reached_multiuser": "reached target multi-user" in low or "reached target graphical" in low,
    "login_prompt": "login:" in low,
    "start_assistant": "setuphelfer" in low and "assistant" in low,
    "kernel_panic": "kernel panic" in low,
    "live_boot_dropped_to_shell": "unable to find a medium" in low or "(initramfs)" in low,
    "nomodeset_active": "nomodeset" in low,
}

# crude "last meaningful line" to see where it stopped
tail = [ln for ln in text.splitlines() if ln.strip()][-25:]

summary = {
    "vm_test": "captured" if text.strip() else "no_serial_output",
    "mode": mode,
    "variant": variant,
    "serial_log": str(log_path),
    "log_bytes": len(text.encode("utf-8")),
    "signals": signals,
    "failed_units": failed_units[:30],
    "failed_error_line_count": len(failed_lines),
    "last_lines": tail,
}
(evdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
