#!/usr/bin/env bash
# 001D7B — verify TUI unit ExecStart/ConditionPathExists match installed runtime names.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT="${REPO_ROOT}/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service"
IMAGE="${REPO_ROOT}/scripts/rescue-live/image"

unit_execstart_exists=false
unit_execstart_executable=false
duplicate_tui_start_paths=0
errors=0

if [[ ! -f "$UNIT" ]]; then
  echo "ERROR: missing unit $UNIT"
  exit 1
fi

if grep -E 'setuphelfer-rescue-tui\.sh|setuphelfer-rescue-entrypoint\.sh' "$UNIT" >/dev/null; then
  echo "ERROR: unit still references .sh runtime path"
  errors=$((errors + 1))
fi

if ! grep -q 'ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui$' "$UNIT" \
  && ! grep -q 'ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui[[:space:]]*$' "$UNIT"; then
  if ! grep -q 'ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui' "$UNIT"; then
    echo "ERROR: ConditionPathExists for setuphelfer-rescue-tui missing"
    errors=$((errors + 1))
  elif grep -q 'ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-tui\.sh' "$UNIT"; then
    echo "ERROR: ConditionPathExists still uses .sh"
    errors=$((errors + 1))
  fi
fi

if ! grep -q 'ExecStart=/usr/local/sbin/setuphelfer-rescue-entrypoint' "$UNIT"; then
  echo "ERROR: ExecStart entrypoint path missing/incorrect"
  errors=$((errors + 1))
fi

# Source files that become installed runtime binaries (repack install -m 0755 strips .sh).
src_tui="${IMAGE}/setuphelfer-rescue-tui.sh"
src_entry="${IMAGE}/setuphelfer-rescue-entrypoint.sh"
_has_shebang() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  head -n 1 "$f" | grep -Eq '^#!/(usr/)?bin/(env )?bash' || head -n 1 "$f" | grep -Eq '^#!/bin/sh'
}
if [[ -f "$src_tui" ]] && _has_shebang "$src_tui"; then
  unit_execstart_exists=true
  unit_execstart_executable=true
else
  echo "ERROR: source TUI script missing or invalid shebang: $src_tui"
  errors=$((errors + 1))
fi
if [[ ! -f "$src_entry" ]] || ! _has_shebang "$src_entry"; then
  echo "ERROR: source entrypoint missing or invalid shebang: $src_entry"
  errors=$((errors + 1))
  unit_execstart_exists=false
  unit_execstart_executable=false
fi

# Duplicate start paths: unit must not list both .sh and non-.sh for same binary.
tui_refs="$(grep -c 'setuphelfer-rescue-tui' "$UNIT" || true)"
if grep -q 'setuphelfer-rescue-tui\.sh' "$UNIT"; then
  duplicate_tui_start_paths=$((duplicate_tui_start_paths + 1))
fi
if [[ "$tui_refs" -gt 4 ]]; then
  # soft signal only; ConditionPathExists + description may repeat tokens
  :
fi

echo "unit_execstart_exists=${unit_execstart_exists}"
echo "unit_execstart_executable=${unit_execstart_executable}"
echo "duplicate_tui_start_paths=${duplicate_tui_start_paths}"

if [[ "$errors" -gt 0 || "$duplicate_tui_start_paths" -ne 0 || "$unit_execstart_exists" != true || "$unit_execstart_executable" != true ]]; then
  exit 1
fi
exit 0
