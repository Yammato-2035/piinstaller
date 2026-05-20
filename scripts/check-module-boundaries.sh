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

# Forbidden: new parallel backup runners under rescue/deploy (backup_runner.py is canonical).
while IFS= read -r -d '' f; do
  case "$f" in
    */tools/backup_runner.py) continue ;;
    */backup_runner.py) warn_msg "unexpected backup_runner: $f" ;;
  esac
done < <(find backend -path '*/venv/*' -prune -o -path '*/.venv/*' -prune -o -name 'backup_runner.py' -print0 2>/dev/null)

# Forbidden: subprocess tar in new rescue modules (deploy runners exempt for sandbox).
if [[ -d backend/rescue ]]; then
  if rg -l 'subprocess\.(run|Popen).*tar' backend/rescue --glob '*.py' 2>/dev/null | grep -q .; then
    warn_msg "subprocess tar in backend/rescue (use tools/backup_runner.py)"
  fi
fi

# Warn: duplicate lsblk parsers in deploy rescue runners (handoff-only allowed; flag heavy usage).
for f in backend/deploy/runner_rescue_storage_discovery.py; do
  if [[ -f "$f" ]] && rg -q 'def .*lsblk|json\.loads.*lsblk' "$f" 2>/dev/null; then
    if rg -q 'subprocess\.run.*lsblk' "$f" 2>/dev/null; then
      warn_msg "$f runs lsblk directly — prefer core.storage facade (see NO_DUPLICATE_MODULE_RULES.md)"
    fi
  fi
done

# Required architecture docs for rescue stick phase.
for doc in \
  docs/architecture/MONOLITH_BOUNDARY_AUDIT_2026-05-20.md \
  docs/architecture/MODULE_BOUNDARIES_TARGET_2026-05-20.md \
  docs/architecture/NO_DUPLICATE_MODULE_RULES.md \
  docs/rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md; do
  if [[ ! -f "$ROOT/$doc" ]]; then
    warn_msg "missing required doc: $doc"
  fi
done

if [[ "$warn" -ne 0 ]]; then
  echo "check-module-boundaries: finished with warnings (see docs/architecture/NO_DUPLICATE_MODULE_RULES.md)" >&2
  exit 1
fi

echo "check-module-boundaries: OK"
exit 0
