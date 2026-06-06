#!/usr/bin/env bash
# Packaging-Version-Gate: Tauri-Bundle-Dateinamen vs. Projektversion (read-only).
#
# Exit: 0 OK oder Warnung (semver-Projektion dokumentiert)
#       19 Artefakt-Version nicht zuordenbar
#       20 Skript/Workspace-Fehler

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT="${PACKAGING_VERSION_GATE_STRICT:-0}"
PY="$REPO_ROOT/backend/tools/check_packaging_version_gate.py"

log() { printf '%s\n' "$*" >&2; }

if [[ ! -f "$PY" ]]; then
  log "check-packaging-version-gate: tool missing: $PY"
  exit 20
fi

args=(--repo-root "$REPO_ROOT")
if [[ "$STRICT" == "1" ]]; then
  args+=(--strict)
fi

set +e
out="$(python3 "$PY" "${args[@]}" 2>&1)"
rc=$?
set -e

printf '%s\n' "$out" >&2

if [[ "$rc" -eq 19 ]]; then
  log "check-packaging-version-gate: BLOCKED — Artefakt-Version passt nicht zur Projektversion"
  exit 19
fi

if [[ "$rc" -ne 0 ]]; then
  log "check-packaging-version-gate: exit $rc"
  exit 20
fi

if printf '%s\n' "$out" | grep -q '^  warn:'; then
  log "check-packaging-version-gate: WARN — semver-Projektion (Cargo/Tauri); siehe docs/developer/VERSIONING.md#versionsebenen-packaging"
fi

log "check-packaging-version-gate: OK"
exit 0
