#!/bin/bash
# Shared helpers for Setuphelfer rescue live scripts (no secrets in logs).
set -euo pipefail

SETUPHELFER_RESCUE_STATE_DIR="${SETUPHELFER_RESCUE_STATE_DIR:-/run/setuphelfer-rescue}"
SETUPHELFER_RESCUE_TELEMETRY_URL="${SETUPHELFER_RESCUE_TELEMETRY_URL:-http://192.168.178.140:8001}"
SETUPHELFER_RESCUE_ISO_SHA256="${SETUPHELFER_RESCUE_ISO_SHA256:-9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a}"

setuphelfer_rescue_ensure_state_dir() {
  mkdir -p "$SETUPHELFER_RESCUE_STATE_DIR"
  chmod 0750 "$SETUPHELFER_RESCUE_STATE_DIR" 2>/dev/null || true
}

setuphelfer_rescue_is_live() {
  [[ -d /run/live/medium ]] || grep -Eq 'setuphelfer_rescue=1|boot=live' /proc/cmdline 2>/dev/null
}

setuphelfer_rescue_boot_id() {
  if [[ -r /proc/sys/kernel/random/boot_id ]]; then
    tr -d '\n' < /proc/sys/kernel/random/boot_id
    return 0
  fi
  cat /etc/machine-id 2>/dev/null || echo "unknown-boot-id"
}

setuphelfer_rescue_is_qemu() {
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    systemd-detect-virt -q && return 0
  fi
  grep -Eq 'QEMU|VirtualBox|VMware|Bochs|KVM' /sys/class/dmi/id/product_name 2>/dev/null
}

setuphelfer_rescue_has_interactive_tty() {
  [[ -t 0 && -t 1 ]] && [[ "${SETUPHELFER_RESCUE_FORCE_HEADLESS:-}" != "1" ]]
}

setuphelfer_rescue_write_json() {
  local dest="$1"
  local tmp
  tmp="$(mktemp "${dest}.XXXXXX")"
  cat >"$tmp"
  mv -f "$tmp" "$dest"
  chmod 0640 "$dest" 2>/dev/null || true
}

setuphelfer_rescue_payload_hash() {
  python3 - <<'PY'
import json, hashlib, sys
data = json.load(sys.stdin)
data.pop("payload_hash_sha256", None)
body = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
print(hashlib.sha256(body).hexdigest())
PY
}

setuphelfer_rescue_iso_sha256() {
  if [[ -f /run/live/medium/live/filesystem.squashfs.sha256 ]]; then
    awk '{print $1}' /run/live/medium/live/filesystem.squashfs.sha256
    return 0
  fi
  printf '%s\n' "$SETUPHELFER_RESCUE_ISO_SHA256"
}
