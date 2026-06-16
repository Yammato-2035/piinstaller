#!/usr/bin/env bash
# Controlled clean of local live-build working tree only.
# Default: dry-run. With --operator-confirm-clean: remove allowed paths.
#
# Always run from repo root, e.g.:
#   cd /home/volker/piinstaller
#   sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
LOG_DIR="${REPO_ROOT}/build/rescue/logs/controlled-iso-build"
LOG_FILE="${LOG_DIR}/clean-latest.log"
CONFIRM=false
DRY_RUN=true

usage() {
  cat <<EOF
Usage: $0 [--dry-run] [--operator-confirm-clean]

Removes only allowed paths under:
  ${BUILD_ROOT}

Allowed: .build, binary, chroot, cache, local, binary.*, chroot.*, wget-log*

If root-owned files block removal, re-run with sudo:
  cd ${REPO_ROOT}
  sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean

Script path: ${SCRIPT_PATH}

Forbidden: paths outside build tree, /opt, /dev, /media, /mnt, git, apt, dd, mount.
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --operator-confirm-clean)
      CONFIRM=true
      DRY_RUN=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -d "$REPO_ROOT/.git" || -f "$REPO_ROOT/.git" ]] || die "not a git repo: $REPO_ROOT"
BUILD_REAL="$(realpath "$BUILD_ROOT" 2>/dev/null || true)"
[[ -n "$BUILD_REAL" ]] || die "build tree missing: $BUILD_ROOT"
[[ "$BUILD_REAL" == "$(realpath "$REPO_ROOT")"* ]] || die "build tree outside repo"

mkdir -p "$LOG_DIR"
{
  echo "=== clean-controlled-live-build-tree $(date -Is) ==="
  echo "REPO_ROOT=$REPO_ROOT"
  echo "BUILD_ROOT=$BUILD_REAL"
  echo "CONFIRM=$CONFIRM DRY_RUN=$DRY_RUN"
  echo "EUID=$(id -u) USER=$(id -un)"
} | tee "$LOG_FILE"

mapfile -t TARGETS < <(
  cd "$REPO_ROOT"
  PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}" python3 - <<'PY'
from pathlib import Path
from core.rescue_iso_build_permission_policy import default_build_tree, list_clean_targets
for p in list_clean_targets(default_build_tree()):
    print(p)
PY
)

if [[ "${#TARGETS[@]}" -eq 0 ]]; then
  echo "No clean targets found (tree may already be clean)." | tee -a "$LOG_FILE"
  exit 0
fi

ROOT_OWNED=0
for t in "${TARGETS[@]}"; do
  if [[ -e "$t" ]] && [[ "$(stat -c '%u' "$t" 2>/dev/null || echo 1)" == "0" ]]; then
    ROOT_OWNED=$((ROOT_OWNED + 1))
  fi
  echo "TARGET: $t" | tee -a "$LOG_FILE"
done

if [[ "$ROOT_OWNED" -gt 0 && "$(id -u)" -ne 0 ]]; then
  echo "WARN: $ROOT_OWNED target(s) are root-owned. Re-run with sudo for removal." | tee -a "$LOG_FILE"
  if [[ "$CONFIRM" == true ]]; then
    echo "BLOCKED: cannot remove root-owned paths without sudo." | tee -a "$LOG_FILE"
    exit 32
  fi
fi

if [[ "$DRY_RUN" == true ]]; then
  echo "DRY-RUN: would remove ${#TARGETS[@]} path(s). Pass --operator-confirm-clean to apply." | tee -a "$LOG_FILE"
  exit 0
fi

FAILED=0
for t in "${TARGETS[@]}"; do
  [[ -e "$t" ]] || continue
  if rm -rf "$t" 2>>"$LOG_FILE"; then
    echo "REMOVED: $t" | tee -a "$LOG_FILE"
  else
    echo "FAILED: $t" | tee -a "$LOG_FILE"
    FAILED=$((FAILED + 1))
  fi
done

if [[ "$FAILED" -gt 0 ]]; then
  echo "Clean incomplete ($FAILED failures). Try: sudo $0 --operator-confirm-clean" | tee -a "$LOG_FILE"
  exit 32
fi

echo "OK: clean completed" | tee -a "$LOG_FILE"
