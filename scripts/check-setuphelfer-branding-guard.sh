#!/usr/bin/env bash
# Read-only: search for forbidden legacy branding outside allowed paths.
# Exit 0: no disallowed hits. Exit 1: at least one disallowed hit. Exit 2: rg missing.
# Does not install hooks, modify files, or run services.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PAT='pi-installer|pi-installer-frontend|piinstaller|PI_INSTALLER_|de\.pi-installer\.app|/opt/pi-installer|pi-installer\.service'

is_allowed_path() {
  local f="$1"
  if [[ "$f" == docs/evidence/* || "$f" == docs/history/* || "$f" == docs/migration/* \
     || "$f" == docs/knowledge-base/deploy/* || "$f" == changelog/* ]]; then
    return 0
  fi
  if [[ "$f" == */compatibility_aliases.json ]]; then
    return 0
  fi
  if [[ "$f" == "docs/developer/SETUPHELFER_BRANDING_GUARD.md" ]]; then
    return 0
  fi
  if [[ "$f" == "scripts/check-setuphelfer-branding-guard.sh" ]]; then
    return 0
  fi
  if [[ "$f" == "backend/deploy/runner_setuphelfer_branding_guard.py" ]]; then
    return 0
  fi
  if [[ "$f" == "backend/tests/test_deploy_runner_setuphelfer_branding_guard_v1.py" ]]; then
    return 0
  fi
  if [[ "$f" == docs/deploy/*.md ]]; then
    local base u
    base="$(basename "$f")"
    u="${base^^}"
    if [[ "$u" == *BRANDING_GUARD* || "$u" == *ZERO_STATE* || "$u" == *RUNTIME_IDENTIFIER* \
       || "$u" == *LEGACY_IDENTIFIER* || "$u" == *COMPATIBILITY_ALIAS* || "$u" == *SETUPHELFER_IDENTIFIER* \
       || "$u" == *ELIMINATION* || "$u" == *MIGRATION* ]]; then
      return 0
    fi
  fi
  return 1
}

if ! command -v rg >/dev/null 2>&1; then
  echo "check-setuphelfer-branding-guard: ripgrep (rg) not found; install ripgrep for this check." >&2
  exit 2
fi

HITS=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  file="${line%%:*}"
  file="${file#./}"
  if is_allowed_path "$file"; then
    continue
  fi
  echo "disallowed legacy branding: $line" >&2
  HITS=$((HITS + 1))
done < <(rg -n -S "$PAT" --hidden --glob '!.git/*' . 2>/dev/null || true)

if [[ "$HITS" -gt 0 ]]; then
  exit 1
fi
exit 0
