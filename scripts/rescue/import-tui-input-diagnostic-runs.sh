#!/usr/bin/env bash
# Import TUI input diagnostic runs from SETUP_LOGS into the workspace evidence tree.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST_ROOT="${REPO_ROOT}/docs/evidence/rescue/tui-input/runs"
mkdir -p "$DEST_ROOT"

SRC=""
for cand in \
  "$(findmnt -rn -S LABEL=SETUP_LOGS -o TARGET 2>/dev/null || true)" \
  /media/volker/SETUP_LOGS2 \
  /media/*/SETUP_LOGS*; do
  [[ -n "$cand" && -d "$cand" ]] || continue
  if [[ -d "$cand/tui-input-diagnostics" ]]; then
    SRC="$cand/tui-input-diagnostics"
    break
  fi
done

if [[ -z "$SRC" ]]; then
  echo "status=blocked reason=setup_logs_diag_root_missing"
  exit 2
fi

imported=0
already=0
skipped_partial=0
for run in "$SRC"/* "$SRC"/.[!.]*; do
  [[ -e "$run" ]] || continue
  [[ -d "$run" ]] || continue
  name="$(basename "$run")"
  # Ignore atomic staging directories (.<RUN_ID>.partial).
  if [[ "$name" == .* && "$name" == *.partial ]]; then
    echo "status=ignored_partial run=$name"
    skipped_partial=$((skipped_partial + 1))
    continue
  fi
  if [[ "$name" == .* ]]; then
    continue
  fi
  dest="$DEST_ROOT/$name"
  if [[ -d "$dest" ]]; then
    echo "status=already_present run=$name"
    already=$((already + 1))
    continue
  fi
  if [[ ! -f "$run/SHA256SUMS" || ! -f "$run/20-file-manifest.json" ]]; then
    echo "status=manifest_invalid run=$name"
    continue
  fi
  mkdir -p "$dest"
  cp -a "$run"/. "$dest"/
  if (cd "$dest" && sha256sum -c SHA256SUMS >/dev/null 2>&1); then
    echo "status=imported run=$name"
    imported=$((imported + 1))
  else
    echo "status=hash_mismatch run=$name"
    rm -rf "$dest"
  fi
done

echo "imported=$imported already_present=$already skipped_partial=$skipped_partial"
