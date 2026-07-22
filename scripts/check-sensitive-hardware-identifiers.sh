#!/usr/bin/env bash
# Pre-push / pre-commit gate: block raw hardware identifiers (NVMe serials, System UUID, etc.).
# PI-RS-ASUS-CAPTURE-FINALIZE-004
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

BASE_REF="${SENSITIVE_ID_BASE_REF:-}"
if [[ -z "$BASE_REF" ]]; then
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    BASE_REF="origin/main"
  else
    BASE_REF="$(git rev-list --max-parents=0 HEAD | tail -1)"
  fi
fi

TMPDIR_SCAN="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_SCAN"' EXIT

FOUND=0
REPORT=()

note() { REPORT+=("$1"); }

# Paths that must never be committed (stick-local protected raw).
if git ls-files --error-unmatch '**/protected_raw/**' >/dev/null 2>&1; then
  note "tracked_protected_raw_paths"
  FOUND=1
fi
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  note "tracked_protected_raw:$f"
  FOUND=1
done < <(git ls-files | grep -E '(^|/)protected_raw(/|$)' || true)

# Worktree + staged + new commit range vs base
scan_blob() {
  local label="$1"
  local blob="$2"
  # NVMe-ish SerialNumber JSON / smartctl
  if grep -Eiq '"(SerialNumber|serial_number|serial)"[[:space:]]*:[[:space:]]*"[A-Za-z0-9]{8,}"' <<<"$blob"; then
    # Allow masked / hash-only forms
    if ! grep -Eiq '"(SerialNumber|serial_number|serial)"[[:space:]]*:[[:space:]]*"(\[redacted|[A-Za-z0-9*]{0,4}\.\.\.|S\*+)' <<<"$blob"; then
      # Heuristic: skip if value looks like a hash (64 hex) or masked
      if grep -Eiq '"(SerialNumber|serial_number|serial)"[[:space:]]*:[[:space:]]*"[0-9a-f]{64}"' <<<"$blob"; then
        :
      elif grep -Eiq '"(SerialNumber|serial_number|serial)"[[:space:]]*:[[:space:]]*"[^*]*\*{2,}' <<<"$blob"; then
        :
      else
        note "serial_like_json:$label"
        FOUND=1
      fi
    fi
  fi
  # Kernel journal style
  if grep -Eiq 'SerialNumber:[[:space:]]*[A-Za-z0-9]{10,}' <<<"$blob"; then
    if ! grep -Eiq 'SerialNumber:[[:space:]]*\[redacted' <<<"$blob"; then
      note "serial_like_journal:$label"
      FOUND=1
    fi
  fi
  # System UUID raw
  if grep -Eiq '"(system_uuid|product_uuid|board_serial)"[[:space:]]*:[[:space:]]*"[0-9a-fA-F-]{16,}"' <<<"$blob"; then
    if ! grep -Eiq '"(system_uuid|product_uuid|board_serial)"[[:space:]]*:[[:space:]]*"(\[redacted|[0-9a-f]{64}|[^*]*\*{2,})' <<<"$blob"; then
      note "system_id_like:$label"
      FOUND=1
    fi
  fi
}

# Scan worktree tracked + untracked evidence/docs/backend (exclude .git, node_modules, build)
# Heuristic scans are limited to evidence docs (tests may use synthetic serials).
while IFS= read -r -d '' f; do
  case "$f" in
    */.git/*|*/node_modules/*|*/build/*|*/dist/*|*/.venv/*) continue ;;
  esac
  if file -b --mime-type "$f" 2>/dev/null | grep -q '^text\|^application/json'; then
    scan_blob "worktree:$f" "$(head -c 2000000 "$f" 2>/dev/null || true)"
  fi
done < <(find docs/evidence -type f \( -name '*.json' -o -name '*.txt' -o -name '*.md' -o -name '*.log' \) -print0 2>/dev/null || true)

# Staged diff
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  STAGED="$(git diff --cached -U0 2>/dev/null || true)"
  if [[ -n "$STAGED" ]]; then
    scan_blob "staged_diff" "$STAGED"
  fi
fi

# New commits vs base: git grep for SerialNumber: raw pattern in range tip trees is heavy;
# instead scan patch.
if git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  RANGE_DIFF="$(git diff "$BASE_REF"...HEAD 2>/dev/null || true)"
  if [[ -n "$RANGE_DIFF" ]]; then
    scan_blob "range_diff:${BASE_REF}...HEAD" "$RANGE_DIFF"
  fi
fi

# Exact serial scan if operator provides local-only secrets file (never commit this file).
SECRETS_FILE="${SENSITIVE_ID_SECRETS_FILE:-/tmp/asus-004-serial-replacements.txt}"
if [[ -f "$SECRETS_FILE" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    raw="${line%%==>*}"
    [[ -z "$raw" || "$raw" == "$line" ]] && continue
    # worktree
    if git grep -F -n -- "$raw" HEAD -- ':!*.git*' >/dev/null 2>&1; then
      note "exact_raw_identifier_in_HEAD_tree"
      FOUND=1
    fi
    # history of current branch not in base
    if git rev-list "$BASE_REF"..HEAD >/dev/null 2>&1; then
      while IFS= read -r c; do
        if git grep -F -n -- "$raw" "$c" -- >/dev/null 2>&1; then
          note "exact_raw_identifier_in_commit:${c:0:12}"
          FOUND=1
        fi
      done < <(git rev-list "$BASE_REF"..HEAD)
    fi
  done < "$SECRETS_FILE"
fi

echo "check-sensitive-hardware-identifiers"
echo "base_ref=$BASE_REF"
if [[ "$FOUND" -ne 0 ]]; then
  echo "RESULT=FAIL"
  printf '%s\n' "${REPORT[@]}" | sort -u
  exit 1
fi
echo "RESULT=PASS"
exit 0
