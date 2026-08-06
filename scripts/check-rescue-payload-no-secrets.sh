#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

patterns=(
  "telemetry-lab-token"
  "telemetry-lab-hmac-key"
  "Authorization: Bearer"
  "X-API-Key:"
)

found=0

check_blob() {
  local label="$1"
  local blob="$2"
  for pattern in "${patterns[@]}"; do
    if grep -qF "$pattern" <<<"$blob"; then
      echo "secret-like pattern found ($label): $pattern"
      found=1
    fi
  done
}

for sq in build/rescue/filesystem.squashfs.repacked-*; do
  [[ -f "$sq" ]] || continue
  listing="$(unsquashfs -ll "$sq" 2>/dev/null || true)"
  check_blob "$(basename "$sq") listing" "$listing"
done

for dir in dist out payload rootfs artifacts; do
  [[ -d "$dir" ]] || continue
  for pattern in "${patterns[@]}"; do
    if rg -n "$pattern" "$dir" 2>/dev/null; then
      echo "secret-like pattern found in $dir: $pattern"
      found=1
    fi
  done
done

if [[ "$found" -ne 0 ]]; then
  exit 1
fi

echo "rescue payload no-secrets check passed"
