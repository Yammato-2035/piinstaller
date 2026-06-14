#!/usr/bin/env bash
# Read-only: prüft filesystem.squashfs in einer Rescue-Hybrid-ISO.
# Exit 0  = alle Pflichtpunkte
# Exit 10 = Artefakt/Squashfs fehlt
# Exit 11 = Setuphelfer-Bundle/Runtime-Marker fehlt
# Exit 12 = systemd-Enable fehlt
# Exit 13 = Keyboard/Locale/Timezone fehlt
# Exit 14 = Login-/MOTD-Hinweis fehlt
# Exit 15 = systemd-Init-Integration fehlt (Binary oder init= bootappend)
# Exit 16 = systemd-sysv/init-Symlink fehlt (nur wenn init= bootappend fehlt)
# Exit 17 = dbus fehlt
# Exit 20 = Usage
set -euo pipefail

ISO="${1:-}"
if [[ -z "$ISO" || ! -f "$ISO" ]]; then
  echo "Usage: $0 /path/to/binary.hybrid.iso" >&2
  exit 20
fi

fail_missing() { echo "MISSING: $*" >&2; exit 10; }
fail_bundle() { echo "INTEGRATION_GAP: $*" >&2; exit 11; }
fail_systemd() { echo "SYSTEMD_ENABLE_GAP: $*" >&2; exit 12; }
fail_locale() { echo "KEYBOARD_LOCALE_GAP: $*" >&2; exit 13; }
fail_login() { echo "LOGIN_HINT_GAP: $*" >&2; exit 14; }
fail_init_integration() { echo "SYSTEMD_INIT_GAP: $*" >&2; exit 15; }
fail_init_symlink() { echo "SYSTEMD_SYSV_INIT_GAP: $*" >&2; exit 16; }
fail_dbus() { echo "DBUS_GAP: $*" >&2; exit 17; }
fail_agent_import() { echo "RESCUE-QEMU-AGENT-IMPORT-001: $*" >&2; exit 18; }
fail_proxy_host() { echo "RESCUE-QEMU-PROXY-HOST-001: $*" >&2; exit 19; }
fail_autopilot_call() { echo "RESCUE-QEMU-AUTOPILOT-CALL-001: $*" >&2; exit 21; }

command -v unsquashfs >/dev/null || fail_missing "unsquashfs"
command -v xorriso >/dev/null || fail_missing "xorriso"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

xorriso -osirrox on -indev "$ISO" -extract /live/filesystem.squashfs "$WORK/filesystem.squashfs" 2>/dev/null \
  || fail_missing "extract /live/filesystem.squashfs from ISO"

SQ="$WORK/filesystem.squashfs"

squashfs_path_exists() {
  unsquashfs -cat "$SQ" "$1" >/dev/null 2>&1
}

squashfs_grep() {
  local path="$1"
  local pattern="$2"
  unsquashfs -cat "$SQ" "$path" 2>/dev/null | grep -qE "$pattern"
}

squashfs_list_has() {
  unsquashfs -ll "$SQ" 2>/dev/null | grep -qF "$1"
}

# --- Bundle / Runtime (exit 11) ---
squashfs_path_exists 'opt/setuphelfer-rescue/MANIFEST.json' \
  || fail_bundle "/opt/setuphelfer-rescue/MANIFEST.json missing"

squashfs_path_exists 'opt/setuphelfer-rescue/backend/venv/bin/python3' \
  || fail_bundle "bundled backend venv missing"

squashfs_path_exists 'opt/setuphelfer-rescue/frontend/dist/index.html' \
  || fail_bundle "frontend/dist/index.html missing"

squashfs_path_exists 'opt/setuphelfer-rescue/scripts/rescue-live/start-backend-localonly.sh' \
  || fail_bundle "start-backend-localonly.sh missing"

# --- systemd init integration (exit 15/16/17) ---
_systemd_binary=false
for _sd in lib/systemd/systemd usr/lib/systemd/systemd; do
  if squashfs_path_exists "$_sd"; then
    _systemd_binary=true
    break
  fi
done
[[ "$_systemd_binary" == true ]] || fail_init_integration "systemd binary missing in squashfs"

_bootappend_init=false
for _cfg in isolinux/live.cfg ISOLINUX/LIVE.CFG; do
  xorriso -osirrox on -indev "$ISO" -extract "/${_cfg}" "$WORK/live.cfg" 2>/dev/null || continue
  if grep -qE 'init=/lib/systemd/systemd|init=/usr/lib/systemd/systemd' "$WORK/live.cfg" 2>/dev/null; then
    _bootappend_init=true
    break
  fi
done
if [[ "$_bootappend_init" != true ]]; then
  WANTS_DIR="$(dirname "$ISO")/config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service"
  if [[ -L "$WANTS_DIR" ]]; then
    echo "HINT: Build-Tree hat init= fix, ISO bootappend fehlt init=/lib/systemd/systemd — Rebuild nötig." >&2
  fi
  fail_init_integration "isolinux live.cfg missing init=/lib/systemd/systemd bootappend"
fi

if ! squashfs_path_exists 'usr/bin/dbus-daemon' && ! squashfs_path_exists 'usr/lib/dbus-1/dbus-daemon-launch-helper'; then
  if ! squashfs_list_has 'usr/share/dbus-1'; then
    fail_dbus "dbus not present in squashfs"
  fi
fi

if [[ "$_bootappend_init" != true ]]; then
  if ! squashfs_list_has 'sbin/init ->' && ! squashfs_list_has 'usr/sbin/init ->'; then
    if squashfs_list_has 'usr/sbin/init' && ! squashfs_list_has 'usr/sbin/init ->'; then
      fail_init_symlink "/usr/sbin/init is not symlinked to systemd (and no init= bootappend)"
    fi
  fi
fi

# --- systemd units (exit 12) ---
squashfs_path_exists 'etc/systemd/system/setuphelfer-backend.service' \
  || fail_systemd "setuphelfer-backend.service unit missing"

squashfs_path_exists 'etc/systemd/system/setuphelfer.service' \
  || fail_systemd "setuphelfer.service unit missing"

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service'; then
  fail_systemd "setuphelfer-backend.service not enabled (no multi-user.target.wants symlink)"
fi

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer.service'; then
  fail_systemd "setuphelfer.service not enabled (no multi-user.target.wants symlink)"
fi

# --- developer-qemu: autopilot enable (exit 12) — detected via serial bootappend in ISO ---
_developer_qemu_iso=false
for _cfg in isolinux/live.cfg ISOLINUX/LIVE.CFG; do
  xorriso -osirrox on -indev "$ISO" -extract "/${_cfg}" "$WORK/live.cfg" 2>/dev/null || continue
  if grep -q 'console=ttyS0' "$WORK/live.cfg" 2>/dev/null; then
    _developer_qemu_iso=true
    break
  fi
done
if [[ "$_developer_qemu_iso" == true ]]; then
  squashfs_path_exists 'etc/systemd/system/setuphelfer-qemu-smoke-autopilot.service' \
    || fail_systemd "developer-qemu ISO missing setuphelfer-qemu-smoke-autopilot.service"
  if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service'; then
    fail_systemd "setuphelfer-qemu-smoke-autopilot.service not enabled (developer-qemu wants missing)"
  fi
  if ! unsquashfs -cat "$SQ" etc/systemd/system/setuphelfer-qemu-smoke-autopilot.service 2>/dev/null \
    | grep -q '10.0.2.2:8001'; then
    fail_systemd "autopilot unit missing devserver endpoint http://10.0.2.2:8001"
  fi
  squashfs_path_exists 'opt/setuphelfer-rescue/backend/devserver_agent/cli.py' \
    || fail_agent_import "devserver_agent package missing in squashfs (opt/setuphelfer-rescue/backend/devserver_agent/cli.py)"
  squashfs_path_exists 'opt/setuphelfer-rescue/backend/devserver_agent/__init__.py' \
    || fail_agent_import "devserver_agent __init__ missing in squashfs"
  _ap_sh='usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh'
  if squashfs_path_exists "$_ap_sh"; then
    _ap_text="$(unsquashfs -cat "$SQ" "$_ap_sh" 2>/dev/null || true)"
    if ! grep -q 'PYTHONPATH=/opt/setuphelfer-rescue/backend' <<< "$_ap_text"; then
      fail_autopilot_call "autopilot missing PYTHONPATH=/opt/setuphelfer-rescue/backend"
    fi
    if grep -qE 'python3[[:space:]]+-m[[:space:]]+backend\.devserver_agent\.cli' <<< "$_ap_text" \
      && ! grep -q 'PYTHONPATH=/opt/setuphelfer-rescue/backend' <<< "$_ap_text"; then
      fail_autopilot_call "backend.devserver_agent.cli without backend on PYTHONPATH"
    fi
    if grep -qE 'python3[[:space:]]+-m[[:space:]]+devserver_agent\.cli' <<< "$_ap_text" \
      && ! grep -q 'PYTHONPATH=/opt/setuphelfer-rescue/backend' <<< "$_ap_text"; then
      fail_autopilot_call "devserver_agent.cli without backend on PYTHONPATH"
    fi
    if ! grep -qE '(-m[[:space:]]+devserver_agent\.cli|devserver_agent\.cli)' <<< "$_ap_text"; then
      fail_autopilot_call "autopilot must invoke devserver_agent.cli with rescue venv or python3"
    fi
    if ! grep -q 'Host: 127.0.0.1:8000' <<< "$_ap_text"; then
      fail_proxy_host "autopilot health curl missing lab Host header override"
    fi
  else
    fail_autopilot_call "setuphelfer-qemu-smoke-autopilot.sh missing in squashfs"
  fi
  echo "OK: developer-qemu autopilot unit enabled in squashfs"
else
  # Non-serial (standard/developer) ISO: the developer-qemu autopilot must NOT leak in.
  # A stale qemu-smoke-autopilot.service hangs the boot on real hardware (no ttyS0 / no QEMU host). See R8C.
  if squashfs_path_exists 'usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh'; then
    fail_systemd "non-developer-qemu ISO must not contain setuphelfer-qemu-smoke-autopilot.sh (stale developer-qemu artifact, hangs boot on hardware)"
  fi
  if squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service'; then
    fail_systemd "non-developer-qemu ISO must not enable setuphelfer-qemu-smoke-autopilot.service (stale developer-qemu artifact, hangs boot on hardware)"
  fi
  echo "OK: no developer-qemu autopilot leak in standard squashfs"
fi

# --- Keyboard / Locale / Timezone (exit 13) ---
squashfs_path_exists 'etc/default/keyboard' \
  || fail_locale "/etc/default/keyboard missing"

squashfs_grep 'etc/default/keyboard' 'XKBLAYOUT="de"' \
  || fail_locale 'XKBLAYOUT="de" missing in /etc/default/keyboard'

squashfs_path_exists 'etc/vconsole.conf' \
  || fail_locale "/etc/vconsole.conf missing"

squashfs_grep 'etc/vconsole.conf' 'KEYMAP=de-latin1' \
  || fail_locale "KEYMAP=de-latin1 missing in /etc/vconsole.conf"

squashfs_path_exists 'etc/default/locale' \
  || fail_locale "/etc/default/locale missing"

squashfs_grep 'etc/default/locale' 'LANG=de_DE\.UTF-8' \
  || fail_locale "LANG=de_DE.UTF-8 missing in /etc/default/locale"

squashfs_path_exists 'etc/timezone' \
  || fail_locale "/etc/timezone missing"

squashfs_grep 'etc/timezone' 'Europe/Berlin' \
  || fail_locale "Europe/Berlin missing in /etc/timezone"

# --- Login / MOTD (exit 14) ---
_login_ok=false
for _hint in etc/issue etc/motd; do
  if squashfs_grep "$_hint" 'Login: user|Login: user '; then
    if squashfs_grep "$_hint" 'live|Passwort: live|Passwort live'; then
      if squashfs_grep "$_hint" 'setuphelfer-rescue|Setuphelfer Rescue'; then
        _login_ok=true
        break
      fi
    fi
  fi
done
if [[ "$_login_ok" != true ]]; then
  fail_login "user/live login hint missing in /etc/issue or /etc/motd"
fi

echo "OK: rescue ISO squashfs — bundle, systemd init, enabled units, de keyboard/locale, login hints${_developer_qemu_iso:+, developer-qemu autopilot}"
