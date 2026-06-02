#!/usr/bin/env bash
# Read-only Preflight fuer bekannte dpkg/start-stop-daemon-Fallen im controlled live-build tree.
# Exit 0 ok/pre_chroot_ok | 10 missing_build_tree | 11 unsafe_auto_config | 12 unsafe_auto_clean
# 13 forbidden_package | 14 dangerous_path_override | 15 chroot_dpkg_missing
# 16 chroot_start_stop_daemon_missing | 20 review_required
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEFAULT_BUILD_ROOT="$REPO_ROOT/build/rescue/live-build/setuphelfer-rescue-live"
BUILD_ROOT="${1:-$DEFAULT_BUILD_ROOT}"
OUT_JSON="$REPO_ROOT/docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json"
EXPECTED_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

AUTO_CONFIG="$BUILD_ROOT/auto/config"
AUTO_BUILD="$BUILD_ROOT/auto/build"
AUTO_CLEAN="$BUILD_ROOT/auto/clean"
PACKAGE_LIST="$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot"
CHROOT_ROOT="$BUILD_ROOT/chroot"

FORBIDDEN_PACKAGES=(
  parted
  gparted
  testdisk
  ntfs-3g
  network-manager
  avahi-daemon
  nginx
  openssh-server
)

SCAN_GLOBS=(
  "$BUILD_ROOT/auto"
  "$BUILD_ROOT/config/hooks"
  "$BUILD_ROOT/config/includes.chroot/etc"
)

STATUS="ok"
EXIT_CODE=0
SUMMARY="DPKG preflight ok"
CHROOT_STATUS="missing"
ISSUES=()
DANGEROUS_MATCHES=()
FORBIDDEN_PACKAGE_MATCHES=()

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

write_json() {
  local tmp issues_file dangerous_file packages_file
  tmp="$(mktemp)"
  issues_file="$(mktemp)"
  dangerous_file="$(mktemp)"
  packages_file="$(mktemp)"
  printf '%s\n' "${ISSUES[@]-}" > "$issues_file"
  printf '%s\n' "${DANGEROUS_MATCHES[@]-}" > "$dangerous_file"
  printf '%s\n' "${FORBIDDEN_PACKAGE_MATCHES[@]-}" > "$packages_file"
  python3 - "$tmp" "$BUILD_ROOT" "$STATUS" "$EXIT_CODE" "$SUMMARY" "$EXPECTED_PATH" "$CHROOT_STATUS" \
    "$AUTO_CONFIG" "$AUTO_BUILD" "$AUTO_CLEAN" "$PACKAGE_LIST" "$CHROOT_ROOT" \
    "$issues_file" "$dangerous_file" "$packages_file" <<'PY'
import json
import sys
from pathlib import Path

tmp = Path(sys.argv[1])

def split_lines(path_arg: str) -> list[str]:
    path = Path(path_arg)
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

payload = {
    "schema_version": 1,
    "phase": "live_build_dpkg_preflight",
    "build_root": sys.argv[2],
    "status": sys.argv[3],
    "exit_code": int(sys.argv[4]),
    "summary": sys.argv[5],
    "expected_path": sys.argv[6],
    "chroot_status": sys.argv[7],
    "issues": split_lines(sys.argv[13]),
    "dangerous_matches": split_lines(sys.argv[14]),
    "forbidden_package_matches": split_lines(sys.argv[15]),
    "checks": {
        "build_tree_exists": Path(sys.argv[2]).is_dir(),
        "auto_config_path": sys.argv[8],
        "auto_build_path": sys.argv[9],
        "auto_clean_path": sys.argv[10],
        "package_list_path": sys.argv[11],
        "chroot_path": sys.argv[12],
        "expected_path": sys.argv[6],
    },
}
tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
  mkdir -p "$(dirname "$OUT_JSON")"
  install -m 0644 "$tmp" "$OUT_JSON"
  rm -f "$tmp" "$issues_file" "$dangerous_file" "$packages_file"
}

finish() {
  write_json
  echo "STATUS: $STATUS"
  echo "SUMMARY: $SUMMARY"
  [[ "${#ISSUES[@]}" -eq 0 ]] || printf 'ISSUE: %s\n' "${ISSUES[@]}"
  [[ "${#DANGEROUS_MATCHES[@]}" -eq 0 ]] || printf 'DANGEROUS: %s\n' "${DANGEROUS_MATCHES[@]}"
  [[ "${#FORBIDDEN_PACKAGE_MATCHES[@]}" -eq 0 ]] || printf 'PACKAGE: %s\n' "${FORBIDDEN_PACKAGE_MATCHES[@]}"
  exit "$EXIT_CODE"
}

fail() {
  STATUS="$1"
  EXIT_CODE="$2"
  SUMMARY="$3"
  shift 3
  ISSUES+=("$@")
  finish
}

# /opt/setuphelfer-rescue is allowed only as Live ISO runtime PYTHONPATH in
# setuphelfer-dev-agent.service (systemd Environment= line). Every other
# /opt/... usage and PATH override remains blocked.
is_allowed_dangerous_path_match() {
  local match="$1"
  case "$match" in
    *setuphelfer-dev-agent.service:*:Environment=PYTHONPATH=/opt/setuphelfer-rescue)
      return 0
      ;;
  esac
  return 1
}

DANGEROUS_PATH_PATTERN='(^|[^A-Z_])PATH=|export PATH=|env -i|dpkg|start-stop-daemon'

[[ -d "$BUILD_ROOT" ]] || fail "missing_build_tree" 10 "Build-Tree fehlt" "$BUILD_ROOT"
[[ -f "$AUTO_CONFIG" ]] || fail "unsafe_auto_config" 11 "auto/config fehlt" "$AUTO_CONFIG"
[[ -f "$AUTO_BUILD" ]] || fail "unsafe_auto_config" 11 "auto/build fehlt" "$AUTO_BUILD"
[[ -f "$AUTO_CLEAN" ]] || fail "unsafe_auto_clean" 12 "auto/clean fehlt" "$AUTO_CLEAN"
[[ -f "$PACKAGE_LIST" ]] || fail "forbidden_package" 13 "setuphelfer.list.chroot fehlt" "$PACKAGE_LIST"

grep -q 'lb config noauto' "$AUTO_CONFIG" || fail "unsafe_auto_config" 11 "auto/config ohne noauto" "$AUTO_CONFIG"
grep -q 'Use controlled gate before running lb build' "$AUTO_BUILD" || fail "unsafe_auto_config" 11 "auto/build nicht geblockt" "$AUTO_BUILD"
grep -q 'rm -rf .build chroot cache binary local' "$AUTO_CLEAN" || fail "unsafe_auto_clean" 12 "auto/clean entfernt falschen Scope" "$AUTO_CLEAN"
if grep -Eq '^[[:space:]]*lb[[:space:]]+clean([[:space:]]|$)' "$AUTO_CLEAN"; then
  fail "unsafe_auto_clean" 12 "auto/clean rekursiv via lb clean" "$AUTO_CLEAN"
fi

for package in "${FORBIDDEN_PACKAGES[@]}"; do
  if grep -Eq "(^|[[:space:]])${package}([[:space:]]|$)" "$PACKAGE_LIST"; then
    FORBIDDEN_PACKAGE_MATCHES+=("$package in $PACKAGE_LIST")
  fi
done
if [[ "${#FORBIDDEN_PACKAGE_MATCHES[@]}" -gt 0 ]]; then
  fail "forbidden_package" 13 "Verbotenes Paket in setuphelfer.list.chroot" "${FORBIDDEN_PACKAGE_MATCHES[@]}"
fi

for scan_root in "${SCAN_GLOBS[@]}"; do
  [[ -e "$scan_root" ]] || continue
  while IFS= read -r match; do
    [[ -n "$match" ]] || continue
    if is_allowed_dangerous_path_match "$match"; then
      continue
    fi
    DANGEROUS_MATCHES+=("$match")
    if [[ "${#DANGEROUS_MATCHES[@]}" -ge 50 ]]; then
      break
    fi
  done < <(grep -RInE "$DANGEROUS_PATH_PATTERN" "$scan_root" 2>/dev/null || true)
  if [[ "${#DANGEROUS_MATCHES[@]}" -ge 50 ]]; then
    break
  fi
done
if [[ "${#DANGEROUS_MATCHES[@]}" -gt 0 ]]; then
  fail "dangerous_path_override" 14 "PATH-/dpkg-Override im Build-Tree gefunden" "${DANGEROUS_MATCHES[@]}"
fi

if [[ ! -d "$CHROOT_ROOT" ]]; then
  CHROOT_STATUS="missing"
  STATUS="pre_chroot_ok"
  SUMMARY="Preflight ok vor chroot-Erzeugung"
  finish
fi

CHROOT_STATUS="present"
CHROOT_DPKG="$CHROOT_ROOT/usr/bin/dpkg"
CHROOT_SH="$CHROOT_ROOT/bin/sh"
CHROOT_SSD=""
for candidate in "$CHROOT_ROOT/sbin/start-stop-daemon" "$CHROOT_ROOT/usr/sbin/start-stop-daemon"; do
  if [[ -x "$candidate" ]]; then
    CHROOT_SSD="$candidate"
    break
  fi
done

[[ -x "$CHROOT_DPKG" ]] || fail "chroot_dpkg_missing" 15 "dpkg im chroot fehlt oder ist nicht ausführbar" "$CHROOT_DPKG"
[[ -x "$CHROOT_SH" ]] || fail "chroot_dpkg_missing" 15 "sh im chroot fehlt oder ist nicht ausführbar" "$CHROOT_SH"
[[ -n "$CHROOT_SSD" ]] || fail "chroot_start_stop_daemon_missing" 16 "start-stop-daemon im chroot fehlt" \
  "$CHROOT_ROOT/sbin/start-stop-daemon" "$CHROOT_ROOT/usr/sbin/start-stop-daemon"

STATUS="ok"
SUMMARY="DPKG preflight ok; chroot enthält dpkg und start-stop-daemon"
finish
