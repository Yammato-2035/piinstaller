#!/usr/bin/env bash
# Pre-push gate: block raw hardware identifiers for ASUS diagnosis branches.
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

FOUND=0
REPORT=()
note() { REPORT+=("$1"); FOUND=1; }

echo "check-sensitive-hardware-identifiers"
echo "base_ref=$BASE_REF"

# 1) Never track stick-local protected_raw
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  note "tracked_protected_raw:$f"
done < <(git ls-files | grep -E '(^|/)protected_raw(/|$)' || true)

# 2) Exact raw identifiers from local-only secrets map (never commit that file)
SECRETS_FILE="${SENSITIVE_ID_SECRETS_FILE:-/tmp/asus-004-serial-replacements.txt}"
if [[ -f "$SECRETS_FILE" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    raw="${line%%==>*}"
    [[ -z "$raw" || "$raw" == "$line" ]] && continue
    if git grep -F -n -- "$raw" HEAD -- >/dev/null 2>&1; then
      note "exact_raw_identifier_in_HEAD_tree"
    fi
    while IFS= read -r c; do
      [[ -z "$c" ]] && continue
      if git grep -F -n -- "$raw" "$c" -- >/dev/null 2>&1; then
        note "exact_raw_identifier_in_commit:${c:0:12}"
      fi
    done < <(git rev-list "${BASE_REF}..HEAD" 2>/dev/null || true)
  done < "$SECRETS_FILE"
else
  echo "note: no SENSITIVE_ID_SECRETS_FILE at $SECRETS_FILE (exact serial scan skipped)"
fi

# 3) Heuristic only on ASUS rescue evidence (Gabriel path) — require redaction marker
scan_asus_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  local blob
  blob="$(head -c 2000000 "$f" 2>/dev/null || true)"
  [[ -z "$blob" ]] && return 0
  # Alnum serials only (excludes USB-host PCI BDFs like 0000:06:00.3). Redacted tokens allowed.
  if grep -Eiq 'SerialNumber:[[:space:]]*[A-Za-z0-9]{10,}' <<<"$blob"; then
    if ! grep -Eiq 'SerialNumber:[[:space:]]*\[redacted' <<<"$blob"; then
      if grep -Eiq 'SerialNumber:[[:space:]]*0{8,}' <<<"$blob" && ! grep -Eiq 'SerialNumber:[[:space:]]*[A-Za-z1-9][A-Za-z0-9]{9,}' <<<"$blob"; then
        :
      else
        note "asus_serial_like_journal:$f"
      fi
    fi
  fi
  if grep -Eiq '"(SerialNumber|serial)"[[:space:]]*:[[:space:]]*"[A-Za-z0-9]{12,}"' <<<"$blob"; then
    if ! grep -Eiq '"(SerialNumber|serial)"[[:space:]]*:[[:space:]]*"(\[redacted|[^"]*\*{2,}|[0-9a-f]{64})"' <<<"$blob"; then
      note "asus_serial_like_json:$f"
    fi
  fi
}

while IFS= read -r -d '' f; do
  scan_asus_file "$f"
done < <(find docs/evidence/rescue/asus-diag-bind-002 \
            docs/evidence/rescue/asus-physical-diag-003 \
            docs/evidence/rescue/asus-win11-linux-001 \
            docs/evidence/rescue/asus-capture-finalize-004 \
            -type f \( -name '*.json' -o -name '*.txt' -o -name '*.log' \) -print0 2>/dev/null || true)

# 4) Staged diff exact secrets already covered via HEAD/history; also block protected_raw staging
if git diff --cached --name-only 2>/dev/null | grep -E '(^|/)protected_raw(/|$)' >/dev/null; then
  note "staged_protected_raw"
fi

if [[ "$FOUND" -ne 0 ]]; then
  echo "RESULT=FAIL"
  printf '%s\n' "${REPORT[@]}" | sort -u
  exit 1
fi

echo "RESULT=PASS"
exit 0
