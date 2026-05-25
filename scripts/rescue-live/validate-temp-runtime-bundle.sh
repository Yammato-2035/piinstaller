#!/usr/bin/env bash
# Validiert temporäres Rescue-Runtime-Bundle (read-only).
# Exit 0 ok | 10 forbidden | 11 missing | 12 CDN | 13 secret | 20 unknown
set -euo pipefail

BUNDLE="${1:-}"
if [[ -z "$BUNDLE" || ! -d "$BUNDLE" ]]; then
  echo "Usage: $0 /path/to/setuphelfer-rescue-runtime" >&2
  exit 20
fi

fail_missing() { echo "MISSING: $*" >&2; exit 11; }
fail_forbidden() { echo "FORBIDDEN: $*" >&2; exit 10; }
fail_cdn() { echo "CDN: $*" >&2; exit 12; }
fail_secret() { echo "SECRET: $*" >&2; exit 13; }

[[ -f "$BUNDLE/MANIFEST.json" ]] || fail_missing "MANIFEST.json"
[[ -x "$BUNDLE/backend/venv/bin/python3" ]] || fail_missing "backend/venv/bin/python3"
[[ -f "$BUNDLE/frontend/dist/index.html" ]] || fail_missing "frontend/dist/index.html"
[[ -x "$BUNDLE/scripts/rescue-live/start-backend-localonly.sh" ]] || fail_missing "start-backend-localonly.sh"
[[ -x "$BUNDLE/scripts/rescue-live/start-ui-localonly.sh" ]] || fail_missing "start-ui-localonly.sh"
[[ -x "$BUNDLE/scripts/rescue-live/check-localonly.sh" ]] || fail_missing "check-localonly.sh"

while IFS= read -r -d '' f; do
  fail_forbidden "$f"
done < <(find "$BUNDLE" -type f \( \
  -name '*.iso' -o -name '*.img' -o -name '*.qcow2' \
  -o -name 'filesystem.squashfs' -o -name 'initrd.img' -o -name 'vmlinuz' \
  -o -name '.env' \
\) -print0 2>/dev/null)

if find "$BUNDLE" -type d -name node_modules 2>/dev/null | grep -q .; then
  fail_forbidden "node_modules directory"
fi
if find "$BUNDLE" -type d -name __pycache__ 2>/dev/null | grep -q .; then
  fail_forbidden "__pycache__ directory"
fi

if grep -rqE 'fonts\.googleapis\.com|fonts\.gstatic\.com' "$BUNDLE/frontend/dist" 2>/dev/null; then
  fail_cdn "Google Fonts in frontend/dist"
fi

SECRET_PAT='API_KEY=|SECRET=|PASSWORD=|TOKEN=|PRIVATE KEY'
for scan_dir in backend config; do
  [[ -d "$BUNDLE/$scan_dir" ]] || continue
  if grep -rIE "$SECRET_PAT" "$BUNDLE/$scan_dir" \
    --exclude-dir='venv' --exclude-dir='tests' --exclude-dir='.venv-ci' --exclude-dir='.venv' \
    2>/dev/null \
    | grep -v 'your-app-password' \
    | grep -v 'BEGIN OPENSSH' \
    | grep -v 're.search(r"API_KEY=|SECRET=|PASSWORD=|TOKEN=|PRIVATE KEY"' \
    | head -1 | grep -q .; then
    fail_secret "pattern match in $scan_dir"
  fi
done

python3 - "$BUNDLE/MANIFEST.json" <<'PY' || exit 20
import json, sys
from pathlib import Path
m = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert m.get("rescue_temp_runtime") is True
assert m.get("no_real_build_execution") is True
assert m.get("files_count", 0) > 0
print(f"OK: manifest files_count={m['files_count']} source_head={m.get('source_head')}")
PY

echo "OK: bundle validation passed"
exit 0
