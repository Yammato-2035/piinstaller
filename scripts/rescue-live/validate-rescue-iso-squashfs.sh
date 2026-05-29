#!/usr/bin/env bash
# Read-only: prüft filesystem.squashfs in einer Rescue-Hybrid-ISO.
# Exit 0  = alle Pflichtpunkte
# Exit 10 = Artefakt/Squashfs fehlt
# Exit 11 = Setuphelfer-Bundle/Runtime-Marker fehlt
# Exit 12 = systemd-Enable fehlt
# Exit 13 = Keyboard/Locale/Timezone fehlt
# Exit 14 = Login-/MOTD-Hinweis fehlt
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

# --- Bundle / Runtime (exit 11) ---
squashfs_path_exists 'opt/setuphelfer-rescue/MANIFEST.json' \
  || fail_bundle "/opt/setuphelfer-rescue/MANIFEST.json missing"

squashfs_path_exists 'opt/setuphelfer-rescue/backend/venv/bin/python3' \
  || fail_bundle "bundled backend venv missing"

squashfs_path_exists 'opt/setuphelfer-rescue/frontend/dist/index.html' \
  || fail_bundle "frontend/dist/index.html missing"

squashfs_path_exists 'opt/setuphelfer-rescue/scripts/rescue-live/start-backend-localonly.sh' \
  || fail_bundle "start-backend-localonly.sh missing"

# --- systemd (exit 12) ---
squashfs_path_exists 'etc/systemd/system/setuphelfer-backend.service' \
  || fail_systemd "setuphelfer-backend.service unit missing"

squashfs_path_exists 'etc/systemd/system/setuphelfer.service' \
  || fail_systemd "setuphelfer.service unit missing"

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service'; then
  WANTS_DIR="$(dirname "$ISO")/config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service"
  if [[ -L "$WANTS_DIR" ]]; then
    echo "HINT: Build-Tree hat Enable-Symlink, ISO ist vermutlich VOR prepare/Rebuild gebaut." >&2
    echo "      ISO: $(stat -c '%y' "$ISO" 2>/dev/null || echo '?')" >&2
    echo "      Tree: $(stat -c '%y' "$WANTS_DIR" 2>/dev/null || echo '?') — Operator: prepare + lb build erneut." >&2
  fi
  fail_systemd "setuphelfer-backend.service not enabled (no multi-user.target.wants symlink)"
fi

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer.service'; then
  fail_systemd "setuphelfer.service not enabled (no multi-user.target.wants symlink)"
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

if squashfs_grep 'etc/issue' 'root.*gesperrt|root-Konsole'; then
  : "root not advertised as login"
elif ! squashfs_grep 'etc/motd' 'root'; then
  : "ok: no false root login promise"
fi

echo "OK: rescue ISO squashfs — bundle, enabled units, de keyboard/locale, login hints"
