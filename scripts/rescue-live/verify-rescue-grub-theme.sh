#!/usr/bin/env bash
# Verify Setuphelfer GRUB theme staging in live-build tree (Phase R.4 — no ISO build).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_ROOT="${SETUPHELFER_RESCUE_BUILD_ROOT:-${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live}"
THEME_DIR="${BUILD_ROOT}/config/includes.binary/boot/grub/themes/setuphelfer"
ISOLINUX_DIR="${BUILD_ROOT}/config/bootloaders/isolinux"

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

_ok=0
_warn=0
_fail=0
_report=()

note() { _report+=("$1"); echo "$1"; }

check_file() {
  local path="$1" label="$2"
  if [[ -f "$path" ]]; then
    note "OK: ${label}: ${path}"
    return 0
  fi
  note "FAIL: missing ${label}: ${path}"
  _fail=$((_fail + 1))
  return 1
}

check_grep() {
  local file="$1" pattern="$2" label="$3"
  if [[ -f "$file" ]] && grep -qE "$pattern" "$file" 2>/dev/null; then
    note "OK: ${label} in ${file}"
    return 0
  fi
  note "WARN: ${label} not found in ${file:-missing}"
  _warn=$((_warn + 1))
  return 1
}

[[ -d "$BUILD_ROOT" ]] || die "build root missing: ${BUILD_ROOT}" 22

check_file "${THEME_DIR}/theme.txt" "grub theme.txt"

if [[ -f "${THEME_DIR}/theme.txt" ]]; then
  _img="$(grep -E '^desktop-image:' "${THEME_DIR}/theme.txt" | sed 's/.*"\(.*\)".*/\1/' || true)"
  if [[ -n "$_img" ]]; then
    check_file "${THEME_DIR}/${_img}" "theme desktop-image reference"
  else
    note "WARN: theme.txt without desktop-image"
    _warn=$((_warn + 1))
  fi
fi

_grub_cfgs=()
while IFS= read -r cfg; do
  _grub_cfgs+=("$cfg")
done < <(find "$BUILD_ROOT" -name 'grub.cfg' 2>/dev/null || true)

if [[ ${#_grub_cfgs[@]} -eq 0 ]]; then
  note "WARN: no grub.cfg in build tree yet (pre-lb build)"
  _warn=$((_warn + 1))
else
  for cfg in "${_grub_cfgs[@]}"; do
    check_grep "$cfg" 'theme|themes/setuphelfer|set theme' "grub theme reference" || true
    check_grep "$cfg" 'menuentry.*Setuphelfer' "Setuphelfer menuentry" || true
  done
fi

if [[ -f "${ISOLINUX_DIR}/isolinux.cfg" ]]; then
  note "OK: ISOLINUX fallback config present: ${ISOLINUX_DIR}/isolinux.cfg"
  check_grep "${ISOLINUX_DIR}/isolinux.cfg" 'label|menu' "isolinux menu labels" || true
else
  note "WARN: ISOLINUX config missing (run prepare-controlled-live-build-tree.sh)"
  _warn=$((_warn + 1))
fi

if [[ -f "${REPO_ROOT}/build/rescue/asset-manifest.json" ]]; then
  note "OK: asset manifest present"
  _ok=$((_ok + 1))
else
  note "WARN: asset manifest missing — run stage-rescue-graphical-assets.sh"
  _warn=$((_warn + 1))
fi

echo ""
echo "=== GRUB theme verification summary ==="
echo "build_root=${BUILD_ROOT}"
echo "fail_count=${_fail}"
echo "warn_count=${_warn}"

if [[ $_fail -gt 0 ]]; then
  exit 10
fi
if [[ $_warn -gt 0 ]]; then
  exit 5
fi
exit 0
