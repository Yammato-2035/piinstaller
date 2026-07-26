#!/usr/bin/env bash
# setuphelfer-g513qm-capture.sh — early/independent capture for G513QM hybrid runs.
# VFAT-safe: invoke via `bash this-script`.
set -uo pipefail

PHASE="${1:-boot_early}"
RUN_ID="${SETUPHELFER_RUN_ID:-}"
SETUP_LOGS_UUID="${SETUP_LOGS_UUID:-9BC7-3950}"

resolve_logs_root() {
  local m
  for m in /media/* /mnt/* /run/media/*/*; do
    [[ -d "$m" ]] || continue
    if [[ -d "$m/setuphelfer" ]] || [[ -d "$m/mint-live" ]]; then
      # Prefer filesystem UUID match when available
      local src
      src="$(findmnt -n -o SOURCE --target "$m" 2>/dev/null || true)"
      if [[ -n "$src" ]]; then
        local uuid
        uuid="$(lsblk -no UUID "$src" 2>/dev/null || true)"
        if [[ "$uuid" == "$SETUP_LOGS_UUID" ]]; then
          echo "$m"
          return 0
        fi
      fi
    fi
  done
  # Fallback: unique SETUP_LOGS label
  local hits=()
  while IFS= read -r line; do hits+=("$line"); done < <(findmnt -n -o TARGET -S LABEL=SETUP_LOGS 2>/dev/null || true)
  if [[ ${#hits[@]} -eq 1 ]]; then
    echo "${hits[0]}"
    return 0
  fi
  if [[ ${#hits[@]} -gt 1 ]]; then
    echo "ERROR: multiple SETUP_LOGS mounts: ${hits[*]}" >&2
    return 2
  fi
  echo ""
  return 1
}

ensure_run() {
  if [[ -z "$RUN_ID" ]]; then
    RUN_ID="g513qm-hybrid-$(date -u +%Y%m%d-%H%M%S)-$(head -c 3 /dev/urandom | xxd -p 2>/dev/null || echo rnd)"
    export SETUPHELFER_RUN_ID="$RUN_ID"
  fi
  RUN_TMP="/run/setuphelfer-capture/${RUN_ID}"
  mkdir -p "$RUN_TMP"/{meta,hardware,boot,kernel,graphics,installer,network,events,final}
  LOGS_ROOT="$(resolve_logs_root || true)"
  if [[ -n "${LOGS_ROOT:-}" ]]; then
    RUN_PERM="${LOGS_ROOT}/setuphelfer/runs/${RUN_ID}"
    mkdir -p "$RUN_PERM"
  else
    RUN_PERM=""
  fi
  echo "$RUN_ID" >"$RUN_TMP/meta/run_id.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ >"$RUN_TMP/meta/last_phase_utc.txt"
  echo "$PHASE" >>"$RUN_TMP/events/timeline.jsonl"
  printf '{"ts":"%s","phase":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PHASE" >>"$RUN_TMP/events/timeline.jsonl"
}

snapshot_common() {
  local d="$RUN_TMP"
  {
    echo "product=$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)"
    echo "board=$(cat /sys/class/dmi/id/board_name 2>/dev/null || true)"
    echo "bios=$(cat /sys/class/dmi/id/bios_version 2>/dev/null || true)"
  } >"$d/hardware/dmi.txt" 2>/dev/null || true
  cat /proc/cmdline >"$d/boot/proc-cmdline.txt" 2>/dev/null || true
  uname -a >"$d/kernel/uname.txt" 2>/dev/null || true
  lsmod >"$d/kernel/loaded-modules.txt" 2>/dev/null || true
  (command -v lspci >/dev/null && lspci -nnk >"$d/hardware/lspci-nnk.txt") 2>/dev/null || echo "lspci_missing" >"$d/hardware/lspci-nnk.txt"
  (mokutil --sb-state >"$d/boot/secure-boot.txt" 2>&1) || echo "mokutil_unavailable" >"$d/boot/secure-boot.txt"
  dmesg >"$d/kernel/dmesg.txt" 2>/dev/null || true
  {
    echo "amdgpu=$(modinfo -F version amdgpu 2>/dev/null || echo absent)"
    echo "nouveau=$(modinfo -F version nouveau 2>/dev/null || echo absent)"
    echo "nvidia=$(modinfo -F version nvidia 2>/dev/null || echo absent)"
    echo "nvidia_vermagic=$(modinfo -F vermagic nvidia 2>/dev/null || echo absent)"
  } >"$d/kernel/module-vermagic.txt" 2>/dev/null || true
  ls /sys/class/drm 2>/dev/null >"$d/graphics/drm-class.txt" || true
  date -u +%Y-%m-%dT%H:%M:%SZ >"$d/meta/heartbeat_utc.txt"
}

sync_to_logs() {
  [[ -n "${RUN_PERM:-}" && -d "$RUN_TMP" ]] || return 0
  mkdir -p "$RUN_PERM"
  cp -a "$RUN_TMP"/. "$RUN_PERM"/ 2>/dev/null || true
  sync || true
}

ensure_run
snapshot_common
echo "capture phase=$PHASE run_id=$RUN_ID logs=${RUN_PERM:-none}"
sync_to_logs
exit 0
