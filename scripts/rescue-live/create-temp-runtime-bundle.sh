#!/usr/bin/env bash
# Erzeugt temporäres Rescue-Runtime-Bundle unter build/rescue/temp-runtime/.
# Kein sudo, apt, mount, ISO, /opt write.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_ROOT="${REPO_ROOT}/build/rescue/temp-runtime"
BUNDLE="${OUT_ROOT}/setuphelfer-rescue-runtime"
STAGE="${OUT_ROOT}/.setuphelfer-rescue-runtime.tmp.$$"

git_workspace() {
  git -c "safe.directory=${REPO_ROOT}" -C "$REPO_ROOT" "$@"
}

SOURCE_HEAD="$(git_workspace rev-parse --short HEAD 2>/dev/null || echo unknown)"

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -d "$REPO_ROOT/backend" ]] || die "backend missing"
[[ -f "$REPO_ROOT/frontend/dist/index.html" ]] || die "frontend/dist missing — run npm run build in frontend first"
[[ -f "$REPO_ROOT/config/version.json" ]] || die "config/version.json missing"

rm -rf "$STAGE"
mkdir -p "$STAGE/scripts/rescue-live" "$STAGE/config" "$STAGE/frontend/dist"

RSYNC_EX=(--exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='*.env'
  --exclude='node_modules' --exclude='.git' --exclude='*.tar.gz' --exclude='*.tar'
  --exclude='*.backup' --exclude='*.restore' --exclude='.pytest_cache'
  --exclude='cache/' --exclude='*.img' --exclude='*.iso' --exclude='*.qcow2'
  --exclude='.venv/' --exclude='.venv-ci/' --exclude='tests/' --exclude='CONFIG.md')

rsync -rlt "${RSYNC_EX[@]}" "$REPO_ROOT/backend/" "$STAGE/backend/"
rsync -rlt "${RSYNC_EX[@]}" "$REPO_ROOT/frontend/dist/" "$STAGE/frontend/dist/"
mkdir -p "$STAGE/scripts/rescue-live"
for _rl in start-backend-localonly.sh start-ui-localonly.sh check-localonly.sh; do
  cp -a "$REPO_ROOT/scripts/rescue-live/$_rl" "$STAGE/scripts/rescue-live/"
done
cp -a "$REPO_ROOT/scripts/serve-frontend-production.py" "$STAGE/scripts/"
cp -a "$REPO_ROOT/config/version.json" "$STAGE/config/"
cp -a "$REPO_ROOT/VERSION" "$STAGE/VERSION"

cat > "$STAGE/README_RESCUE_TEMP_RUNTIME.md" <<EOF
# Setuphelfer Rescue Temp Runtime

- Source HEAD: ${SOURCE_HEAD}
- No sudo, apt, mount, or automatic writes.
- Set \`SETUPHELFER_RESCUE_ROOT\` to this directory.

## Start (local-only)

\`\`\`bash
export SETUPHELFER_RESCUE_ROOT="\$(pwd)"
./scripts/rescue-live/start-backend-localonly.sh
./scripts/rescue-live/start-ui-localonly.sh
./scripts/rescue-live/check-localonly.sh
\`\`\`
EOF

FORBIDDEN_SCAN="$(
  find "$STAGE" -type f \( \
    -name '*.iso' -o -name '*.img' -o -name '*.qcow2' \
    -o -name 'filesystem.squashfs' -o -name 'initrd.img' -o -name 'vmlinuz' \
    -o -name '.env' -o -name 'node_modules' \
  \) 2>/dev/null | head -20
)"

if [[ -n "$FORBIDDEN_SCAN" ]]; then
  echo "$FORBIDDEN_SCAN" >&2
  die "forbidden files in bundle"
fi

python3 - "$STAGE" "$SOURCE_HEAD" "$FORBIDDEN_SCAN" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

bundle = Path(sys.argv[1])
source_head = sys.argv[2]
files: list[dict] = []
for p in sorted(bundle.rglob("*")):
    if not p.is_file():
        continue
    rel = p.relative_to(bundle).as_posix()
    if "__pycache__" in rel or rel.endswith(".pyc"):
        continue
    data = p.read_bytes()
    files.append({
        "path": rel,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

manifest = {
    "schema_version": "1.0",
    "component": "rescue_temp_runtime_bundle_manifest",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "source_head": source_head,
    "files_count": len(files),
    "files": files,
    "forbidden_scan": [],
    "no_real_build_execution": True,
    "rescue_temp_runtime": True,
}
manifest_path = bundle / "MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"MANIFEST: {manifest_path} ({len(files)} files)")
PY

chmod +x "$STAGE/scripts/rescue-live/"*.sh 2>/dev/null || true

if [[ -e "$BUNDLE" ]]; then
  old_bundle="${OUT_ROOT}/.setuphelfer-rescue-runtime.old.$(date +%s).$$"
  mv "$BUNDLE" "$old_bundle"
  rm -rf "$old_bundle" 2>/dev/null || true
fi
mv "$STAGE" "$BUNDLE"
echo "OK: bundle at $BUNDLE"
