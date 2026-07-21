#!/usr/bin/env bash
# Check rescue stick GUI locale files (PI-RS-BVR-GUI-DCC-001).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOC_DIR="${REPO_ROOT}/scripts/rescue-live/image/locales"
REQUIRED=(de-DE en-US fr-FR nl-NL)
missing=0
declare -A KEYS
for loc in "${REQUIRED[@]}"; do
  f="${LOC_DIR}/${loc}.json"
  if [[ ! -f "$f" ]]; then
    echo "MISSING $f"
    missing=1
    continue
  fi
  keys="$(python3 -c "import json,sys; print(','.join(sorted(json.load(open(sys.argv[1],encoding='utf-8')).keys())))" "$f")"
  KEYS["$loc"]="$keys"
  echo "OK $loc keys=$keys"
done
ref="${KEYS[de-DE]:-}"
for loc in "${REQUIRED[@]}"; do
  [[ -n "${KEYS[$loc]:-}" ]] || continue
  if [[ "${KEYS[$loc]}" != "$ref" ]]; then
    echo "KEYSET_MISMATCH $loc"
    missing=1
  fi
done
exit "$missing"
