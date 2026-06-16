#!/usr/bin/env bash
# Build Rescue React UI into build/rescue/ui/ — no npm install, no apt.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FRONTEND="${REPO_ROOT}/frontend"
OUT_DIR="${REPO_ROOT}/build/rescue/ui"
MANIFEST="${OUT_DIR}/rescue-ui-manifest.json"

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

for tool in node npm; do
  command -v "$tool" >/dev/null 2>&1 || {
    cat >"$MANIFEST" <<EOF
{
  "build_status": "blocked_missing_frontend_tool",
  "missing_tool": "$tool",
  "no_fake_green": true
}
EOF
    echo "blocked_missing_frontend_tool: $tool"
    exit 30
  }
done

[[ -d "${FRONTEND}/node_modules" ]] || die "node_modules missing — install frontend deps outside this script" 31

cd "$FRONTEND"
npm run prebuild >/dev/null 2>&1 || true
npx vite build --config vite.rescue.config.ts

SHA=""
if [[ -f "${OUT_DIR}/rescue.html" ]]; then
  SHA="$(sha256sum "${OUT_DIR}/rescue.html" | awk '{print $1}')"
fi

python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

repo = Path(${REPO_ROOT@Q})
version = json.loads((repo / "config/version.json").read_text(encoding="utf-8")).get("project_version", "1.7.10.0")
out = Path(${OUT_DIR@Q})
manifest = {
    "schema_version": 1,
    "ui": "react-rescue-shell",
    "build_status": "success",
    "built_at": datetime.now(tz=timezone.utc).isoformat(),
    "version": version,
    "output_dir": str(out),
    "entry_html": str(out / "rescue.html") if (out / "rescue.html").is_file() else None,
    "entry_sha256": ${SHA@Q} or None,
    "profile": "rescue_ui",
    "offline_first": True,
    "network_required": False,
    "telemetry_required": False,
    "no_fake_green": True,
}
(out / "rescue-ui-manifest.json").write_text(json.dumps(manifest, indent=2) + "\\n", encoding="utf-8")
print(json.dumps({"build_status": "success", "output_dir": str(out), "version": version}))
PY

echo "OK: Rescue React UI built -> ${OUT_DIR}"
