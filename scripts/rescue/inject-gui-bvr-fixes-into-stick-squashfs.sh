#!/usr/bin/env bash
# Inject GUI-BVR blocker fixes into live FAT32 ESP squashfs (no full ISO rebuild).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ESP_MOUNT="${ESP_MOUNT:-}"
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --esp) ESP_MOUNT="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--esp PATH] --execute"; exit 0 ;;
    *) echo "Unknown: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$ESP_MOUNT" ]]; then
  for cand in /tmp/setuphelfer-efi-rw /media/*/SETUPHELFER; do
    [[ -f "${cand}/live/filesystem.squashfs" ]] && ESP_MOUNT="$cand" && break
  done
fi
[[ -n "$ESP_MOUNT" ]] || { echo "ESP not found" >&2; exit 1; }
SQ="${ESP_MOUNT}/live/filesystem.squashfs"
[[ -f "$SQ" ]] || { echo "missing $SQ" >&2; exit 1; }
[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute"; exit 0; }

WORK="$(mktemp -d /tmp/setuphelfer-sq-inject.XXXXXX)"
ROOT="${WORK}/root"
trap 'rm -rf "$WORK"' EXIT

echo "[INFO] unsquashfs → ${ROOT}"
unsquashfs -f -d "$ROOT" "$SQ" >/dev/null

inject() {
  local src="$1" dst="$2"
  # Optional workspace modules may be untracked/absent; skip rather than abort
  # the whole repack. Required diagnostic paths are verified after injects.
  if [[ ! -e "$src" ]]; then
    echo "[SKIP] missing source: $src"
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
  echo "[OK] $dst"
}

BE="${ROOT}/opt/setuphelfer-rescue/backend"
IMG="${ROOT}/opt/setuphelfer-rescue/scripts/rescue-live/image"
SBIN="${ROOT}/usr/local/sbin"

inject "${REPO_ROOT}/backend/core/rescue_tui_backup_plan_body.py" \
  "${BE}/core/rescue_tui_backup_plan_body.py"
inject "${REPO_ROOT}/backend/core/rescue_backup_plan_contract.py" \
  "${BE}/core/rescue_backup_plan_contract.py"
inject "${REPO_ROOT}/backend/core/rescue_msi_boot_profile.py" \
  "${BE}/core/rescue_msi_boot_profile.py"
inject "${REPO_ROOT}/backend/core/rescue_asus_rog_boot_profile.py" \
  "${BE}/core/rescue_asus_rog_boot_profile.py"
inject "${REPO_ROOT}/backend/core/rescue_asus_rog_lab_boot.py" \
  "${BE}/core/rescue_asus_rog_lab_boot.py"
inject "${REPO_ROOT}/backend/core/rescue_pi5_lab.py" \
  "${BE}/core/rescue_pi5_lab.py"
inject "${REPO_ROOT}/backend/core/rescue_test_matrix.py" \
  "${BE}/core/rescue_test_matrix.py"

# Sync ALL backend/core/rescue_*.py so Backup-Plan / E2E never miss imports (e.g. windows_backup_scope).
mkdir -p "${BE}/core"
shopt -s nullglob
for py in "${REPO_ROOT}/backend/core"/rescue_*.py; do
  inject "$py" "${BE}/core/$(basename "$py")"
done
shopt -u nullglob

# Physical E2E CLI + helpers (TUI menu "E2E").
inject "${REPO_ROOT}/backend/core/rescue_wifi_diagnostics.py" \
  "${BE}/core/rescue_wifi_diagnostics.py"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-physical-e2e" \
  "${IMG}/setuphelfer-rescue-physical-e2e"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-physical-e2e-start-gate" \
  "${IMG}/setuphelfer-rescue-physical-e2e-start-gate"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-tui.sh" \
  "${IMG}/setuphelfer-rescue-tui.sh"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-tui-input-diagnostic" \
  "${IMG}/setuphelfer-rescue-tui-input-diagnostic"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-tui-input-diagnostic" \
  "${SBIN}/setuphelfer-rescue-tui-input-diagnostic"
# Git may store the CLI as non-executable (100644); force runtime +x in squash.
chmod +x "${IMG}/setuphelfer-rescue-tui-input-diagnostic" \
  "${SBIN}/setuphelfer-rescue-tui-input-diagnostic" 2>/dev/null || true
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-input-diagnostic.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-input-diagnostic.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-live-medium-check.py" \
  "${IMG}/setuphelfer-rescue-live-medium-check.py"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-media-check" \
  "${IMG}/setuphelfer-rescue-media-check"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-media-check.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-media-check.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-common.sh" \
  "${IMG}/setuphelfer-rescue-common.sh"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh" \
  "${IMG}/setuphelfer-rescue-gui-watchdog.sh"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-auto-physical-e2e" \
  "${IMG}/setuphelfer-rescue-auto-physical-e2e"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-auto-e2e-tui-display.py" \
  "${IMG}/setuphelfer-rescue-auto-e2e-tui-display.py"
inject "${REPO_ROOT}/backend/core/rescue_canonical_bvr_progress.py" \
  "${BE}/core/rescue_canonical_bvr_progress.py"
inject "${REPO_ROOT}/backend/core/rescue_auto_e2e_gui_status.py" \
  "${BE}/core/rescue_auto_e2e_gui_status.py"
inject "${REPO_ROOT}/config/rescue_payload_version.json" \
  "${ROOT}/opt/setuphelfer-rescue/config/rescue_payload_version.json"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh" \
  "${IMG}/setuphelfer-rescue-entrypoint.sh"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-asus-rog-bios-gate" \
  "${IMG}/setuphelfer-rescue-asus-rog-bios-gate"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-hardware-discovery" \
  "${IMG}/setuphelfer-rescue-hardware-discovery"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-auto-win11-setup-log-capture-start-gate" \
  "${IMG}/setuphelfer-rescue-auto-win11-setup-log-capture-start-gate"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-auto-win11-setup-log-capture-runner" \
  "${IMG}/setuphelfer-rescue-auto-win11-setup-log-capture-runner"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-win11-setup-log-capture.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-auto-win11-setup-log-capture.service"
inject "${REPO_ROOT}/backend/core/rescue_auto_win11_setup_log_capture.py" \
  "${BE}/core/rescue_auto_win11_setup_log_capture.py"
inject "${REPO_ROOT}/backend/core/rescue_hardware_discovery_capture.py" \
  "${BE}/core/rescue_hardware_discovery_capture.py"
inject "${REPO_ROOT}/backend/core/rescue_asus_lab_authorization.py" \
  "${BE}/core/rescue_asus_lab_authorization.py"
inject "${REPO_ROOT}/backend/core/rescue_bitlocker_mutation_guard.py" \
  "${BE}/core/rescue_bitlocker_mutation_guard.py"
inject "${REPO_ROOT}/backend/core/rescue_win11_live_capture.py" \
  "${BE}/core/rescue_win11_live_capture.py"
inject "${REPO_ROOT}/backend/core/rescue_lab_job_contract.py" \
  "${BE}/core/rescue_lab_job_contract.py"
inject "${REPO_ROOT}/backend/api/routes/rescue_asus_lab_control.py" \
  "${BE}/api/routes/rescue_asus_lab_control.py"
inject "${REPO_ROOT}/config/lab-targets/asus-rog-gabriel.yaml" \
  "${ROOT}/opt/setuphelfer-rescue/config/lab-targets/asus-rog-gabriel.yaml"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-pi5-lab" \
  "${IMG}/setuphelfer-rescue-pi5-lab"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-tui-deadline" \
  "${IMG}/setuphelfer-rescue-tui-deadline"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-kiosk-start" \
  "${IMG}/setuphelfer-rescue-kiosk-start"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-ui-launch" \
  "${IMG}/setuphelfer-rescue-ui-launch"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-ui-http-server" \
  "${IMG}/setuphelfer-rescue-ui-http-server"
inject "${REPO_ROOT}/scripts/rescue-live/image/setuphelfer-rescue-ui-http-server" \
  "${SBIN}/setuphelfer-rescue-ui-http-server"
inject "${REPO_ROOT}/scripts/rescue-live/image/auto-e2e-progress.html" \
  "${ROOT}/usr/share/setuphelfer/rescue/ui/auto-e2e-progress.html"
mkdir -p "${ROOT}/usr/share/setuphelfer/rescue/ui/locales"
for loc in de-DE en-US fr-FR nl-NL; do
  inject "${REPO_ROOT}/scripts/rescue-live/image/locales/${loc}.json" \
    "${ROOT}/usr/share/setuphelfer/rescue/ui/locales/${loc}.json"
done
# WinPE / Windows Setup log collector (FAT32-readable copy also synced into image tree)
inject "${REPO_ROOT}/scripts/rescue-live/image/SETUPHELFER_WIN_DIAG" \
  "${IMG}/SETUPHELFER_WIN_DIAG"
inject "${REPO_ROOT}/scripts/rescue-live/image/SETUPHELFER_WIN_DIAG" \
  "${ROOT}/usr/share/setuphelfer/rescue/SETUPHELFER_WIN_DIAG"
chmod +x "${IMG}/setuphelfer-rescue-ui-http-server" "${SBIN}/setuphelfer-rescue-ui-http-server" 2>/dev/null || true
inject "${REPO_ROOT}/backend/api/routes/rescue.py" \
  "${BE}/api/routes/rescue.py"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-hold.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-hold.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-start-assistant.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-start-assistant.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-deadline.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-deadline.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-deadline.timer" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-deadline.timer"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-discovery.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-auto-discovery.service"
mkdir -p "${ROOT}/etc/systemd/system/multi-user.target.wants"
mkdir -p "${ROOT}/etc/systemd/system/basic.target.wants"
mkdir -p "${ROOT}/etc/systemd/system/timers.target.wants"
ln -sf ../setuphelfer-rescue-tui.service \
  "${ROOT}/etc/systemd/system/basic.target.wants/setuphelfer-rescue-tui.service"
ln -sf ../setuphelfer-rescue-tui.service \
  "${ROOT}/etc/systemd/system/multi-user.target.wants/setuphelfer-rescue-tui.service"
ln -sf ../setuphelfer-rescue-tui-deadline.timer \
  "${ROOT}/etc/systemd/system/timers.target.wants/setuphelfer-rescue-tui-deadline.timer"
ln -sf ../setuphelfer-rescue-tui-deadline.timer \
  "${ROOT}/etc/systemd/system/basic.target.wants/setuphelfer-rescue-tui-deadline.timer"
ln -sf ../setuphelfer-rescue-auto-win11-setup-log-capture.service \
  "${ROOT}/etc/systemd/system/multi-user.target.wants/setuphelfer-rescue-auto-win11-setup-log-capture.service"
# Drop debug probe if a previous inject left it enabled.
rm -f "${ROOT}/etc/systemd/system/basic.target.wants/setuphelfer-rescue-tui-probe.service" \
  "${ROOT}/etc/systemd/system/multi-user.target.wants/setuphelfer-rescue-tui-probe.service" \
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-probe.service"
# Keep copies under image/systemd in sync for diagnostics.
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service" \
  "${IMG}/systemd/setuphelfer-rescue-tui.service"
inject "${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-start-assistant.service" \
  "${IMG}/systemd/setuphelfer-rescue-start-assistant.service"

# Keep /usr/local/sbin wrappers/scripts in sync when they are copies.
for name in setuphelfer-rescue-tui setuphelfer-rescue-common.sh \
            setuphelfer-rescue-gui-watchdog setuphelfer-rescue-gui-watchdog.sh \
            setuphelfer-rescue-entrypoint setuphelfer-rescue-entrypoint.sh \
            setuphelfer-rescue-asus-rog-bios-gate setuphelfer-rescue-pi5-lab \
            setuphelfer-rescue-hardware-discovery \
            setuphelfer-rescue-auto-win11-setup-log-capture-start-gate \
            setuphelfer-rescue-auto-win11-setup-log-capture-runner \
            setuphelfer-rescue-tui-deadline \
            setuphelfer-rescue-physical-e2e setuphelfer-rescue-physical-e2e-start-gate \
            setuphelfer-rescue-auto-physical-e2e \
            setuphelfer-rescue-auto-e2e-tui-display.py \
            setuphelfer-rescue-kiosk-start setuphelfer-rescue-ui-launch \
            setuphelfer-rescue-ui-http-server \
            setuphelfer-rescue-media-check setuphelfer-rescue-live-medium-check.py; do
  if [[ -e "${SBIN}/${name}" ]] || [[ -e "${IMG}/${name}" ]] || [[ -e "${IMG}/${name}.sh" ]]; then
    src=""
    if [[ -f "${IMG}/${name}.sh" ]]; then
      src="${IMG}/${name}.sh"
    elif [[ -f "${IMG}/${name}" ]]; then
      src="${IMG}/${name}"
    fi
    if [[ -n "$src" ]]; then
      # Prefer .sh payload; strip .sh for the sbin runtime name when needed.
      dst_name="$name"
      [[ "$dst_name" == *.sh && "$dst_name" != "setuphelfer-rescue-common.sh" ]] && dst_name="${dst_name%.sh}"
      cp -a "$src" "${SBIN}/${dst_name}"
      # cp -a can preserve a non-exec mode from stale unsquashed copies — force +x.
      case "$dst_name" in
        setuphelfer-rescue-common.sh|setuphelfer-rescue-live-medium-check.py) ;;
        *) chmod +x "${SBIN}/${dst_name}" ;;
      esac
    fi
  fi
done
chmod +x "${IMG}/setuphelfer-rescue-tui.sh" \
  "${IMG}/setuphelfer-rescue-gui-watchdog.sh" \
  "${IMG}/setuphelfer-rescue-entrypoint.sh" \
  "${IMG}/setuphelfer-rescue-kiosk-start" \
  "${IMG}/setuphelfer-rescue-ui-launch" \
  "${IMG}/setuphelfer-rescue-ui-http-server" \
  "${IMG}/setuphelfer-rescue-media-check" 2>/dev/null || true
chmod +x "${SBIN}/setuphelfer-rescue-media-check" \
  "${SBIN}/setuphelfer-rescue-ui-http-server" 2>/dev/null || true
# Mirror executable scripts under image/ without .sh where the live image expects them.
for pair in \
  "setuphelfer-rescue-tui.sh:setuphelfer-rescue-tui" \
  "setuphelfer-rescue-gui-watchdog.sh:setuphelfer-rescue-gui-watchdog" \
  "setuphelfer-rescue-entrypoint.sh:setuphelfer-rescue-entrypoint"; do
  src="${IMG}/${pair%%:*}"
  dst="${IMG}/${pair##*:}"
  if [[ -f "$src" ]]; then
    cp -a "$src" "$dst"
    chmod +x "$dst"
  fi
done

# Required for PI-RS-TUI-AUTO (fail closed if diagnostic payload incomplete).
REQUIRED_IN_ROOT=(
  "${BE}/core/rescue_tui_input_diagnostic.py"
  "${BE}/core/rescue_tui_input_diagnostic_contract.py"
  "${SBIN}/setuphelfer-rescue-tui-input-diagnostic"
  "${ROOT}/etc/systemd/system/setuphelfer-rescue-tui-input-diagnostic.service"
  "${IMG}/setuphelfer-rescue-tui.sh"
)
for req in "${REQUIRED_IN_ROOT[@]}"; do
  if [[ ! -e "$req" ]]; then
    echo "[ERROR] required inject missing in squash root: $req" >&2
    exit 1
  fi
done
echo "[OK] required TUI diagnostic inject paths present"

# Payload version stamp — keep all carriers in sync (VERSION + both JSON files).
python3 - <<PY
import json
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, str(Path(${REPO_ROOT@Q}) / "backend"))
from core.rescue_payload_version_carriers import (
    build_rescue_payload_version_json,
    build_rescue_runtime_version_json,
)
cfg = Path(${REPO_ROOT@Q}) / "config/rescue_payload_version.json"
data = json.loads(cfg.read_text(encoding="utf-8"))
ver = data["rescue_payload_version"]
root = Path(${ROOT@Q})
# VERSION
vp = root / "opt/setuphelfer-rescue/VERSION"
vp.parent.mkdir(parents=True, exist_ok=True)
vp.write_text(ver + "\n", encoding="utf-8")
# rescue_payload_version.json
payload = build_rescue_payload_version_json(ver)
payload.update({k: data[k] for k in data if k.startswith("pi_rs_")})
payload["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload["update_method"] = "gui_bvr_blocker_inject"
rp = root / "opt/setuphelfer-rescue/config/rescue_payload_version.json"
rp.parent.mkdir(parents=True, exist_ok=True)
rp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
# version.json carrier (project_version == payload)
vj = root / "opt/setuphelfer-rescue/config/version.json"
vj.write_text(json.dumps(build_rescue_runtime_version_json(ver), indent=2) + "\n", encoding="utf-8")
# enable diagnostic unit
wants = root / "etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True, exist_ok=True)
unit = root / "etc/systemd/system/setuphelfer-rescue-tui-input-diagnostic.service"
link = wants / "setuphelfer-rescue-tui-input-diagnostic.service"
if unit.is_file():
    if link.exists() or link.is_symlink():
        link.unlink()
    # Relative Wants link (absolute temp paths break after mksquashfs).
    link.symlink_to("../setuphelfer-rescue-tui-input-diagnostic.service")
print("payload", ver)
PY

# NTFS RO for Panther: Debian bookworm ntfs-3g (live kernel has CONFIG_NTFS3_FS=n).
# Never inject host Ubuntu 24.04 ntfs-3g — it needs GLIBC_2.38 and breaks on Debian 12 live.
echo "[INFO] inject Debian-bookworm-compatible ntfs-3g + fuse3…"
NTFS_VENDOR="${REPO_ROOT}/scripts/rescue/vendor/ntfs-3g-debian-bookworm"
mkdir -p "${ROOT}/usr/bin" "${ROOT}/bin" "${ROOT}/usr/sbin" "${ROOT}/sbin" \
  "${ROOT}/lib/x86_64-linux-gnu" "${ROOT}/usr/lib/x86_64-linux-gnu"
if [[ -x "${NTFS_VENDOR}/usr/bin/ntfs-3g" || -x "${NTFS_VENDOR}/bin/ntfs-3g" ]]; then
  _ntfs_bin="${NTFS_VENDOR}/usr/bin/ntfs-3g"
  [[ -x "$_ntfs_bin" ]] || _ntfs_bin="${NTFS_VENDOR}/bin/ntfs-3g"
  cp -a "$_ntfs_bin" "${ROOT}/usr/bin/ntfs-3g"
  cp -a "$_ntfs_bin" "${ROOT}/bin/ntfs-3g"
  chmod 755 "${ROOT}/usr/bin/ntfs-3g" "${ROOT}/bin/ntfs-3g"
  ln -sfn /usr/bin/ntfs-3g "${ROOT}/usr/sbin/mount.ntfs-3g"
  ln -sfn /usr/bin/ntfs-3g "${ROOT}/sbin/mount.ntfs-3g"
  if [[ -e "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libntfs-3g.so.89" ]]; then
    cp -a "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libntfs-3g.so.89"* \
      "${ROOT}/lib/x86_64-linux-gnu/" || true
    cp -a "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libntfs-3g.so.89"* \
      "${ROOT}/usr/lib/x86_64-linux-gnu/" || true
  fi
  if [[ -x "${NTFS_VENDOR}/usr/bin/fusermount3" ]]; then
    cp -a "${NTFS_VENDOR}/usr/bin/fusermount3" "${ROOT}/usr/bin/fusermount3"
    cp -a "${NTFS_VENDOR}/usr/bin/fusermount3" "${ROOT}/bin/fusermount3" 2>/dev/null || true
    chmod 755 "${ROOT}/usr/bin/fusermount3" 2>/dev/null || true
  fi
  if [[ -e "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libfuse3.so.3" ]]; then
    cp -aL "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libfuse3.so.3"* \
      "${ROOT}/lib/x86_64-linux-gnu/" || true
    cp -aL "${NTFS_VENDOR}/lib/x86_64-linux-gnu/libfuse3.so.3"* \
      "${ROOT}/usr/lib/x86_64-linux-gnu/" || true
  fi
  # Prove binary does not require GLIBC newer than 2.36 (Debian 12).
  if command -v readelf >/dev/null 2>&1; then
    if readelf -V "${ROOT}/usr/bin/ntfs-3g" 2>/dev/null | grep -qE 'Name: GLIBC_2\.(3[8-9]|[4-9][0-9])'; then
      echo "[ERROR] injected ntfs-3g still requires GLIBC >= 2.38" >&2
      exit 1
    fi
  fi
  echo "[OK] bookworm ntfs-3g + fuse3 injected from vendor"
else
  echo "[ERROR] missing vendor ntfs-3g at ${NTFS_VENDOR}" >&2
  exit 1
fi

# NetworkManager refuses plugins not owned by root (squashfs inject can preserve wrong uid).
# Without this, WiFi is only a generic device — breaks multi-host WLAN.
echo "[INFO] fix NetworkManager plugin ownership…"
NM_PLUGIN_DIRS=(
  "${ROOT}/usr/lib/x86_64-linux-gnu/NetworkManager"
  "${ROOT}/usr/lib/NetworkManager"
)
for _nm_base in "${NM_PLUGIN_DIRS[@]}"; do
  [[ -d "$_nm_base" ]] || continue
  find "$_nm_base" -type f -name 'libnm-device-plugin-*.so' -print0 2>/dev/null \
    | while IFS= read -r -d '' _plug; do
        chown root:root "$_plug" 2>/dev/null || true
        chmod 644 "$_plug" 2>/dev/null || true
      done
done

OUT="${WORK}/filesystem.squashfs.new"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "[INFO] mksquashfs…"
mksquashfs "$ROOT" "$OUT" -comp xz -noappend -no-xattrs >/dev/null
SHA="$(sha256sum "$OUT" | awk '{print $1}')"
# Prefer host backup; ESP backups fill the 4G FAT quickly.
HOST_BACKUP="/tmp/filesystem.squashfs.pre-gui-bvr-${STAMP}"
cp -a "$SQ" "$HOST_BACKUP"
FREE_KB="$(df -Pk "$(dirname "$SQ")" | awk 'NR==2{print $4}')"
NEED_KB=$(( $(stat -c%s "$OUT") / 1024 + 102400 ))
if [[ "${FREE_KB:-0}" -lt "$NEED_KB" ]]; then
  echo "[WARN] ESP free ${FREE_KB}KiB < need ~${NEED_KB}KiB — removing old ESP squashfs backups"
  rm -f "$(dirname "$SQ")"/filesystem.squashfs.pre-gui-bvr-* || true
fi
cp -a "$OUT" "$SQ"
echo "$SHA" >"${SQ}.sha256"
sync
echo "[OK] squashfs updated sha256=${SHA}"
echo "[OK] host_backup=${HOST_BACKUP}"
