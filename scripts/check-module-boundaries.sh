#!/usr/bin/env bash
# Warn-only guard: duplicate module patterns before rescue stick growth.
# Exit 0 = no warnings; 1 = warnings (CI may enable later).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

warn=0
warn_msg() {
  echo "check-module-boundaries: WARNING: $*" >&2
  warn=1
}

# --- Canonical backup runner ---
while IFS= read -r -d '' f; do
  case "$f" in
    */tools/backup_runner.py) continue ;;
    */backup_runner.py) warn_msg "unexpected backup_runner: $f" ;;
  esac
done < <(find backend -path '*/venv/*' -prune -o -path '*/.venv/*' -prune -o -name 'backup_runner.py' -print0 2>/dev/null)

# --- Forbidden subprocess tar in rescue package (deploy runners exempt legacy) ---
if [[ -d backend/rescue ]]; then
  if rg -l 'subprocess\.(run|Popen).*\btar\b' backend/rescue --glob '*.py' 2>/dev/null | grep -q .; then
    warn_msg "subprocess tar in backend/rescue (use tools/backup_runner.py)"
  fi
fi

# --- lsblk/findmnt allowlist (core + legacy); warn on new usage elsewhere ---
LSBLK_ALLOW=(
  "backend/core/storage_facade.py"
  "backend/core/safe_device.py"
  "backend/modules/storage_detection.py"
  "backend/core/device_identity.py"
  "backend/core/rescue_hardstop.py"
  "backend/debug/support_bundle.py"
)
FINDMNT_ALLOW=(
  "backend/core/mount_facade.py"
  "backend/core/safe_device.py"
  "backend/modules/storage_detection.py"
  "backend/core/backup_target_auto_prepare.py"
  "backend/modules/inspect_storage.py"
  "backend/modules/rescue_restore_execute.py"
  "backend/core/rescue_hardstop.py"
)

is_allowed() {
  local file="$1"
  shift
  local allowed
  for allowed in "$@"; do
    if [[ "$file" == "$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

scan_pattern() {
  local pattern="$1"
  local label="$2"
  shift 2
  local allow=("$@")
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if is_allowed "$f" "${allow[@]}"; then
      continue
    fi
    if rg -q "$pattern" "$f" 2>/dev/null; then
      warn_msg "$label in $f (use core.storage_facade / core.mount_facade)"
    fi
  done < <(
    rg -l "$pattern" backend/app.py backend/deploy backend/rescue backend/inspect --glob '*.py' 2>/dev/null || true
  )
}

scan_pattern 'subprocess\.(run|Popen).*\blsblk\b' "direct lsblk subprocess" "${LSBLK_ALLOW[@]}"
scan_pattern 'subprocess\.(run|Popen).*\bfindmnt\b' "direct findmnt subprocess" "${FINDMNT_ALLOW[@]}"

# mount/umount execution outside allowlist
MOUNT_EXEC_ALLOW=(
  "backend/core/mount_facade.py"
  "backend/core/backup_target_auto_prepare.py"
)
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if is_allowed "$f" "${MOUNT_EXEC_ALLOW[@]}"; then
    continue
  fi
  if rg -q "subprocess\.(run|Popen).*\b(mount|umount)\b" "$f" 2>/dev/null; then
    warn_msg "mount/umount subprocess in $f"
  fi
done < <(
  rg -l "subprocess\.(run|Popen).*\b(mount|umount)\b" backend/app.py backend/deploy backend/rescue --glob '*.py' 2>/dev/null || true
)

# Required architecture docs
for doc in \
  docs/architecture/MONOLITH_BOUNDARY_AUDIT_2026-05-20.md \
  docs/architecture/MODULE_BOUNDARIES_TARGET_2026-05-20.md \
  docs/architecture/NO_DUPLICATE_MODULE_RULES.md \
  docs/architecture/MODULE_FREEZE_REGISTER_2026-05-20.md \
  docs/architecture/CORE_STORAGE_MOUNT_FACADES_2026-05-20.md \
  docs/rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md; do
  if [[ ! -f "$ROOT/$doc" ]]; then
    warn_msg "missing required doc: $doc"
  fi
done

for mod in backend/core/storage_facade.py backend/core/mount_facade.py; do
  if [[ ! -f "$ROOT/$mod" ]]; then
    warn_msg "missing facade module: $mod"
  fi
done

if [[ "$warn" -ne 0 ]]; then
  echo "check-module-boundaries: finished with warnings (see docs/architecture/NO_DUPLICATE_MODULE_RULES.md)" >&2
  exit 1
fi

echo "check-module-boundaries: OK"
exit 0
